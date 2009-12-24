=======================
zojax:content directive
=======================

Alternative implementation of content types system.

   >>> import zojax.content.type
   >>> from zojax.content.type import interfaces, constraints, item, tests

   >>> from zope.configuration import xmlconfig
   >>> context = xmlconfig.file('meta.zcml', zojax.content.type)

We can register new content type with `zojax:content` directive.
Let's create schema and implementation for our type.

   >>> from zope import interface, component, schema

   >>> class IMyContent(interface.Interface):
   ...     
   ...     title = schema.TextLine(
   ...         title = u'Title')
   ...     param2 = schema.TextLine(
   ...         title = u'Param2')

   >>> class MyContent(item.Item):
   ...     interface.implements(IMyContent)
   ...     
   ...     def __init__(self, title, description=u'', param=''):
   ...         self.title = title
   ...         self.description = description
   ...         self.param = param

   >>> context = xmlconfig.string("""
   ... <configure xmlns:zojax="http://namespaces.zope.org/zojax" i18n_domain="zojax">
   ...   <zojax:content
   ...     name="myContent"
   ...     title="My content"
   ...     class="zojax.content.TESTS.MyContent"
   ...     schema="zojax.content.TESTS.IMyContent"
   ...     description="Simple content type." />
   ... </configure>""", context)

We can get content type as named utility.

   >>> ctContent = component.getUtility(interfaces.IContentType, 'myContent')

   >>> ctContent.name, ctContent.klass, ctContent.title
   (u'myContent', <class 'zojax.content.TESTS.MyContent'>, u'My content')

We can create content instance

   >>> content = ctContent.create(u'Title')
   >>> isinstance(content, MyContent)
   True

Content type for content object

   >>> print interfaces.IContentType(content)
   <BoundContentType:zojax.content.type.contenttype.ContentType myContent 'My content'>


Content Type binding
--------------------

We can use content types for various tasks like adding new content, 
check availability of content type, etc. Content type should be bound to 
some context

   >>> interfaces.IBoundContentType.providedBy(ctContent)
   False

   >>> print ctContent
   <ContentType:zojax.content.type.contenttype.ContentType myContent 'My content'>

Now we need content

   >>> from zope.app.container.sample import SampleContainer
   >>> container = SampleContainer()

Now let's bind content type to container

   >>> bctContent = ctContent.__bind__(container)
   
   >>> interfaces.IBoundContentType.providedBy(bctContent)
   True

   >>> print bctContent
   <BoundContentType:zojax.content.type.contenttype.ContentType myContent 'My content'>


Content Type availability
-------------------------

Unbound content type is always unavailable. By default zojax.content register only
one checker for permission checks.

   >>> ctContent.isAvailable()
   False

   >>> bctContent.isAvailable()
   True

We can define new avilability checks. We need new adapter to IContentTypeChecker
interface. We define checker that fail is content type name is 'failed.container'

   >>> class NameChecker(object):
   ...    interface.implements(interfaces.IContentTypeChecker)
   ...    component.adapts(interfaces.IContentType, interface.Interface)
   ...    
   ...    def __init__(self, contenttype, context):
   ...        self.contenttype = contenttype
   ...        self.context = context
   ...
   ...    def check(self):
   ...        return not (self.contenttype.name == 'failed.container')

   >>> component.provideAdapter(NameChecker, name='mychecker')

   >>> bctContent.name = 'failed.container'
   >>> bctContent.isAvailable()
   False

   >>> bctContent.name = 'any'
   >>> bctContent.isAvailable()
   True

   >>> sm = component.getSiteManager()
   >>> t = sm.unregisterAdapter(NameChecker, name='mychecker')


Adding Content
--------------

We can add content only if container content type can contain content types.
Let's register container content type

   >>> from zojax.content.type.container import ContentContainer

   >>> class IMyContainer(interfaces.IItem):
   ...     pass

   >>> class MyContainer(ContentContainer):
   ...     interface.implements(IMyContainer)

   >>> context = xmlconfig.string("""
   ... <configure xmlns:zojax="http://namespaces.zope.org/zojax" i18n_domain="zojax">
   ...   <zojax:content
   ...     name="myContainer"
   ...     title="My container"
   ...     class="zojax.content.TESTS.MyContainer"
   ...     schema="zojax.content.TESTS.IMyContainer"
   ...     description="Simple container type." />
   ... </configure>""", context)

   >>> ctContainer = component.getUtility(interfaces.IContentType, 'myContainer')

Unbound container can't contain any content

   >>> list(ctContainer.listContainedTypes())
   []

   >>> container = MyContainer('Container')

   >>> bctContainer = ctContainer.__bind__(container)
   >>> [ct.name for ct in bctContainer.listContainedTypes()]
   [u'myContent', u'myContainer']

   >>> content = ctContent.create('Title')

Content type 'create' method determine content constructor arguments,
also it set schema fields

   >>> ctContent.klass = None
   >>> content = ctContent.create('Title')
   Traceback (most recent call last):
   ...
   ValueError: Can't create content type: 'myContent'

   >>> ctContent.klass = MyContent

   >>> c = ctContent.create(param='param', param2='param2')
   Traceback (most recent call last):
   ...
   TypeError: Not enough arguments

   >>> c = ctContent.create('Title', param='param', param2='param2')
   >>> c, c.param, c.param2
   (<zojax.content.TESTS.MyContent ...>, 'param', 'param2')


We can't add content with unbound content type

   >>> ctContent.add(content, 'test-content')
   Traceback (most recent call last):
   ...
   Unauthorized: Can't create 'myContent' instance

   >>> bctContent = ctContent.__bind__(container)
   >>> addedContent = bctContent.add(content, 'test-content')
   >>> addedContent.__name__
   u'test-content'

   >>> container[u'test-content'] is content
   True

But if conten type not in container content type types listing we won't 
able to add content.

   >>> interface.directlyProvides(ctContent, interfaces.IInactiveType)
   >>> t = sm.unregisterUtility(ctContent, interfaces.IActiveType, ctContent.name)
   
   >>> [ct.name for ct in bctContainer.listContainedTypes()]
   [u'myContainer']

   >>> content = ctContent.create(u'Title')
   
   >>> addedContent = bctContent.add(content, 'test-content2')
   Traceback (most recent call last):
   ...
   InvalidItemType: ...


ContentType Type
----------------

We can use any number of types in type attribute of directive. 
By default package defines some types.

IInactiveType - for inactive types, this type can't be added to any container
also if we won't use 'factory' then content type marked as inactive automaticly

   >>> ct = component.getUtility(interfaces.IContentType, 'myContent')
   >>> interfaces.IInactiveType.providedBy(ct)
   True

   >>> [ct.name for ct in bctContainer.listContainedTypes()]
   [u'myContainer']


IActiveType - for content that can be added to any content container

   >>> class IContent1(interfaces.IItem):
   ...     pass

   >>> class Content1(item.Item):
   ...     interface.implements(IContent1)

   >>> context = xmlconfig.string("""
   ... <configure xmlns:zojax="http://namespaces.zope.org/zojax" i18n_domain="zojax">
   ...   <zojax:content
   ...     name="content1"
   ...     title="content1"
   ...     schema="zojax.content.TESTS.IContent1"
   ...     class="zojax.content.TESTS.Content1"
   ...     type="zojax.content.type.interfaces.IActiveType"
   ...     description="Simple content type." />
   ... </configure>""", context)

   >>> [ct.name for ct in bctContainer.listContainedTypes()]
   [u'myContainer', u'content1']


`IExplicitlyAddable` - if content type is explicitly addable then it can be added 
only to container that explicitly contains content type

   >>> class IContent2(interfaces.IItem):
   ...     pass

   >>> class Content2(item.Item):
   ...     interface.implements(IContent2)

   >>> context = xmlconfig.string("""
   ... <configure xmlns:zojax="http://namespaces.zope.org/zojax" i18n_domain="zojax">
   ...   <zojax:content
   ...     name="content2"
   ...     title="content2"
   ...     schema="zojax.content.TESTS.IContent2"
   ...     class="zojax.content.TESTS.Content2"
   ...     type="zojax.content.type.tests.ITestContentType
   ...           zojax.content.type.interfaces.IExplicitlyAddable"
   ...     description="Simple content type." />
   ... </configure>""", context)

   >>> [ct.name for ct in bctContainer.listContainedTypes()]
   [u'myContainer', u'content1']

Now let's add content type to precondition, it is the same if we use
`contains="mypackage.interface.IMyType"`

   >>> precondition = component.getUtility(
   ...     constraints.IItemTypePrecondition, bctContainer.name)
   >>> precondition.ifaces.append(tests.ITestContentType)

   >>> [ct.name for ct in bctContainer.listContainedTypes()]
   [u'myContainer', u'content1', u'content2']
