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
""" IContentType implementation

$Id$
"""
import types

from zope import interface, event
from zope.component import getAdapters, queryUtility, getUtilitiesFor

from zope.location import Location
from zope.proxy import removeAllProxies
from zope.lifecycleevent import ObjectCreatedEvent
from zope.security.interfaces import Unauthorized
from zope.security.proxy import removeSecurityProxy

from zope.app.container.constraints import \
     IItemTypePrecondition, IContainerTypesConstraint
from zope.app.container.interfaces import \
     IAdding, INameChooser, IContainerNamesContainer
from zope.app.container.interfaces import InvalidItemType, InvalidContainerType

from interfaces import _
from interfaces import IContentType, IBoundContentType
from interfaces import IContentContainer, IContentTypeChecker
from interfaces import IActiveType, IInactiveType, IExplicitlyAddable
from interfaces import IContentNamesContainer

from constraints import checkObject


class ContentType(Location):
    interface.implements(IContentType)

    __name__ = ''
    __parent__ = None

    context = None

    def __init__(self, name, schema, klass,
                 title, description, permission='zojax.AddContent',
                 addform=None):
        self.name = name
        self.schema = schema
        self.klass = klass
        self.title = title
        self.description = description
        self.permission = permission
        self.addform = addform

        # args,kwargs for klass constructor
        if klass is None or type(klass.__init__) != types.MethodType:
            self.factoryArgs = ()
            self.factoryNames = ()
            return

        func = klass.__init__.im_func
        code = func.func_code
        names = code.co_varnames[1:code.co_argcount]

        if not func.func_defaults:
            self.factoryArgs = names
            self.factoryNames = ()
        else:
            num = len(names)- len(func.func_defaults)
            self.factoryArgs = names[:num]
            self.factoryNames = names[num:]

    def __bind__(self, context):
        clone = self.__class__.__new__(self.__class__)
        clone.__dict__.update(self.__dict__)
        clone.context = context
        if context is not None:
            interface.alsoProvides(clone, IBoundContentType)
        return clone

    def __str__(self):
        if IBoundContentType.providedBy(self):
            return "<BoundContentType:%s.%s %s '%s'>"%(
                self.__class__.__module__, self.__class__.__name__,
                self.name, self.title)
        else:
            return "<ContentType:%s.%s %s '%s'>"%(
                self.__class__.__module__, self.__class__.__name__,
                self.name, self.title)

    @property
    def container(self):
        return self.context

    def checkObject(self, container, name, content):
        return checkObject(container, name, content)

    def add(self, content, name=''):
        if not self.isAddable():
            raise Unauthorized("Can't create '%s' instance"%self.name)

        context = self.container
        content = removeAllProxies(content)

        if IContentContainer.providedBy(context) or \
                IContentNamesContainer.providedBy(content):
            chooser = INameChooser(context)

            if IContainerNamesContainer.providedBy(context):
                name = chooser.chooseName('', content)
            else:
                name = chooser.chooseName(name, content)
                chooser.checkName(name, content)

            self.checkObject(context, name, content)

            removeSecurityProxy(context)[name] = content
            return context[name]
        else:
            raise ValueError(_("Can't add content."))

    def create(self, *args, **data):
        if self.klass is None:
            raise ValueError("Can't create content type: '%s'"%self.name)

        # prepare arguments
        args = list(args)
        for name in self.factoryArgs[len(args):]:
            if name not in data:
                raise TypeError('Not enough arguments')

        kwargs = {}
        for name in self.factoryNames:
            if name in data:
                kwargs[name] = data[name]

        # create content
        content = self.klass(*args, **kwargs)

        # set content attributes
        schema = self.schema
        args = self.factoryArgs
        names = self.factoryNames
        for name, value in data.items():
            if name not in args and name not in names:
                if name in self.schema:
                    field = schema[name].bind(content)
                    field.set(content, value)

        event.notify(ObjectCreatedEvent(content))
        return content

    def isAddable(self):
        if not IBoundContentType.providedBy(self) or \
                IInactiveType.providedBy(self):
            return False

        for name, adapter in getAdapters(
            (self, self.context), IContentTypeChecker):
            if not adapter.check():
                return False
        else:
            return True

    def isAvailable(self):
        if not IBoundContentType.providedBy(self) or \
                IInactiveType.providedBy(self):
            return False

        for name, adapter in getAdapters(
            (self, self.context), IContentTypeChecker):
            if not adapter.check():
                return False
        else:
            return True

    def listContainedTypes(self, checkAvailability=True):
        if IBoundContentType.providedBy(self):
            context = self.context
            if not IContentContainer.providedBy(context):
                return

            precondition = IItemTypePrecondition(self, None)

            if precondition is not None:
                contenttypes = []
                for tp in precondition.types:
                    ct = queryUtility(IContentType, tp)
                    if ct is not None and ct not in contenttypes:
                        contenttypes.append(ct)

                for tp in precondition.ifaces:
                    for name, ct in getUtilitiesFor(tp):
                        if ct not in contenttypes:
                            contenttypes.append(ct)

                for contenttype in contenttypes:
                    contenttype = contenttype.__bind__(context)

                    explicit = True
                    if IExplicitlyAddable.providedBy(contenttype):
                        explicit = False
                        for tp in precondition.ifaces:
                            if tp not in (IActiveType, IExplicitlyAddable)\
                                    and tp.providedBy(contenttype):
                                explicit = True
                                break

                        for tp in precondition.types:
                            if contenttype.name == tp:
                                explicit = True
                                break

                    if explicit:
                        # check the container constraint
                        validate = queryUtility(
                            IContainerTypesConstraint, contenttype.name)
                        if validate is not None:
                            try:
                                validate(self)

                                if not checkAvailability:
                                    yield contenttype

                                elif contenttype.isAvailable():
                                    yield contenttype
                            except InvalidContainerType:
                                pass
                        else:
                            if not checkAvailability:
                                yield contenttype

                            elif contenttype.isAvailable():
                                yield contenttype
