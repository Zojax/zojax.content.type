##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" content types system implementation

$Id$
"""
from zope import schema, interface
from zope.i18nmessageid import MessageFactory

_ = MessageFactory('zojax.content.type')


class WrongContentType(Exception):
    """ wrong content type """


class UnremovableContent(Exception):
    """ unremovable content """


class NameReserved(Exception):
    """ name reserved """


class PublishingDatesError(schema.interfaces.ValidationError):
    __doc__ = _("""Publishing dates are wrong.""")


class IItem(interface.Interface):
    """ Simple item """

    title = schema.TextLine(
        title = _(u'Title'),
        description = _(u'Item title.'),
        default = u'',
        missing_value = u'',
        required = True)

    description = schema.Text(
        title = _(u'Description'),
        description = _(u'Brief summary of your content item.'),
        default = u'',
        missing_value = u'',
        required = False)


class IItemPublishing(interface.Interface):

    effective = schema.Datetime(
        title = _(u'Effective Date'),
        description = _(u'The date when the item will be published. '
                        u'If no date is selected the item will be published immediately.'),
        required = False)

    expires = schema.Datetime(
        title = _(u'Expiration Date'),
        description = _(u'The date when the item expires. '
                        u'This will automatically make the item invisible '
                        u'for others at the given date. '
                        u'If no date is chosen, it will never expire.'),
        required = False)

    publishcomment = schema.Text(
        title = _(u'Comment'),
        description = _(u'Comment will be added to the publishing history.'),
        required = False)

    @interface.invariant
    def effectiveExpiresDates(item):
        effective = getattr(item, 'effective', None)
        expires = getattr(item, 'expires', None)
        if (effective is None or expires is None) or (effective >= expires):
            raise PublishingDatesError()


class IContent(interface.Interface):
    """ marker interface for content types """


class IDraftedContent(interface.Interface):
    """ Marker interface for drafted content """


class ISearchableContent(interface.Interface):
    """ marker interface for searchable content """


class IShareableContent(interface.Interface):
    """ marker interface for shareable content """


class IUnremoveableContent(interface.Interface):
    """ marker interface for content item that can't be
    removed from container """


class IContentContainer(interface.Interface):
    """ container for content """


class IOrderAware(interface.Interface):
    """ order aware container """


class IAnnotatableOrder(IOrderAware):
    """ store order information in annotation """


class IOrder(interface.Interface):
    """ container contents order """

    def addItem(name):
        """ add item to order """

    def removeItem(name):
        """ remove item to order """

    def rebuild():
        """ rebuild order """

    def nextKey(key=None):
        """Return the next key.

        If a key argument if provided and not None, return the next key in order.
        Raise an exception if
        no such key exists.
        """

    def previousKey(key=None):
        """Return the previous key.

        If a key argument if provided and not None, return the previous key in order.
        Raise an exception if
        no such key exists.
        """
        
    def keyPosition(key=None):
        """Return the key position.

        If a key argument if provided and not None, return the key position in order.
        Raise an exception if
        no such key exists.
        """


class IReordable(interface.Interface):
    """ reordable contents """

    def moveUp(names):
        """ move items up """

    def moveDown(names):
        """ move items down """

    def moveTop(names):
        """ move items top """

    def moveBottoms(names):
        """ move items bottom """

    def updateOrder(order):
        """ update container order """


class IReservedNames(interface.Interface):
    """A list of reserved name,
    that can be used as item name in content container """

    names = schema.Tuple(
        title = u'Names',
        description = u'Not allowed names as item name',
        required = True)


class IContentType(interface.Interface):

    name = schema.TextLine(
        title = _(u'Name'),
        description = _(u'Content Type Name'),
        required = True)

    title = schema.TextLine(
        title = _(u'Title'),
        description = _(u'Content Type Title'),
        required = True)

    description = schema.Text(
        title = _(u'Description'),
        description = _(u'Content Type Description'),
        required = False)

    schema = interface.Attribute('Schema')
    context = interface.Attribute('Context')
    klass = interface.Attribute('Class')
    addform = interface.Attribute('Custom add form')
    container = interface.Attribute('Adding container')

    def __bind__(context):
        """ bind to context """

    def add(content, name=''):
        """ add content to container """

    def checkObject(container, name, content):
        """ check content in container """

    def create(**data):
        """ create content """

    def isAdable():
        """ addable in context """

    def isAvailable():
        """ available in context """

    def listContainedTypes(checkAvailability=True):
        """ list availabel content types allowed for adding """


class IBoundContentType(interface.Interface):
    """ bound content type """


class IContentTypeChecker(interface.Interface):
    """ check if content type withing context """

    def __init__(contenttype, context):
        """ init """

    def check():
        """ check """


class IContentTypeType(interface.interfaces.IInterface):
    """ content type type """


class IActiveType(interface.Interface):
    """ active content type """


class IInactiveType(interface.Interface):
    """ inactive content type """


class IPortalType(interface.Interface):
    """ portal type """


class IActivePortalType(IPortalType, IActiveType):
    """ active portal type """


class IExplicitlyAddable(interface.Interface):
    """ implicite addable, container type should explicitly define
    this content type as containable """


class IExplicitlyContained(interface.Interface):
    """ container type, content type should explicitly define
    this container type as container """


class IContentView(interface.Interface):
    """ marker interface for content view """


class IContentPreview(interface.Interface):
    """ marker interface for content preview """


class IContentViewView(interface.Interface):
    """ content view - view name """

    name = interface.Attribute('View name')


class IRenameNotAllowed(interface.Interface):
    """ marker interface for content that doesn't support renaming """


class IEmptyNamesNotAllowed(interface.Interface):
    """ marker interface """


class IContainerContentsAware(interface.Interface):
    """ allow manage container contents """


class IContainerContentsTable(interface.Interface):
    """ container contents table """


class IContentNamesContainer(interface.Interface):
    """ container should select content name """


class IContentTitleAction(interface.Interface):
    """ container should select content name """


class ITitleBasedName(interface.Interface):
    """ title based name chooser """


class INameChooserConfiglet(interface.Interface):
    """ configlet interface """

    short_url_enabled = schema.Bool(
        title = _(u'Short-url generation'),
        description = _(u'Enable short-url generation.'),
        default = True,
        required = False)

    limit_words = schema.Int(
        title = _(u'Limit words count'),
        description = _(u'Limit words count.'),
        default = 5,
        required = False)
