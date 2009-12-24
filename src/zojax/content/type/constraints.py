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
"""

$Id$
"""
from zope import interface, component
from zope.component import queryUtility
from zope.app.container.constraints import \
    IItemTypePrecondition, IContainerTypesConstraint
from zope.app.container.interfaces import \
    InvalidItemType, InvalidContainerType, IWriteContainer

from interfaces import IContent
from interfaces import IContentType, IContentContainer
from interfaces import IExplicitlyAddable


def checkObject(container, name, object):
    """Check containement constraints for an object and container"""
    if not (IWriteContainer.providedBy(container) or
            IContentContainer.providedBy(container)):
        raise TypeError('Container is not a valid Zope container.')

    # check item precondition
    precondition = contains(container)
    if precondition is not None:
        precondition(container, name, object)
    else:
        contenttype = IContentType(object, None)
        if contenttype is None:
            raise InvalidItemType(container, object, ())

    # check the container constraint
    validate = containers(object)
    if validate is not None:
        validate(container)


def checkContentType(container, contenttype):
    if not (IWriteContainer.providedBy(container) or
            IContentContainer.providedBy(container)) :
        raise TypeError('Container is not a valid Zope container.')

    ct = IContentType(container, None)
    if ct is None:
        raise InvalidContainerType(container)

    # check item precondition
    precondition = ctContains(ct)
    if precondition is not None:
        precondition(container, '', contenttype)

    # check the container constraint
    validate = queryUtility(IContainerTypesConstraint, contenttype.name)
    if validate is not None:
        validate(container)


class ItemTypePrecondition(object):
    interface.implements(IItemTypePrecondition)

    def __init__(self, ifaces=[], types=[]):
        self.types = list(types)
        self.ifaces = list(ifaces)

    def __call__(self, container, name, object):
        contenttype = IContentType(object, None)

        if contenttype is not None:
            if contenttype.name in self.types:
                return True

            for iface in self.ifaces:
                if iface.providedBy(contenttype):
                    return True

        raise InvalidItemType(
            container, (object, contenttype), (self.types, self.ifaces), name)


@component.adapter(IContent)
@interface.implementer(IItemTypePrecondition)
def contains(context):
    contenttype = IContentType(context, None)

    if contenttype is not None:
        return queryUtility(IItemTypePrecondition, contenttype.name)


@component.adapter(IContentType)
@interface.implementer(IItemTypePrecondition)
def ctContains(contenttype):
    return queryUtility(IItemTypePrecondition, contenttype.name)


class ContainerTypesConstraint(object):
    interface.implements(IContainerTypesConstraint)

    def __init__(self, ifaces=[], types=[]):
        self.types = list(types)
        self.ifaces = list(ifaces)

    def __call__(self, container):
        if IContentType.providedBy(container):
            contenttype = container
        else:
            contenttype = IContentType(container, None)
            if contenttype is None:
                raise InvalidContainerType(container, self.types)

        if contenttype.name in self.types:
            return True

        for iface in self.ifaces:
            if iface.providedBy(contenttype):
                return True

        raise InvalidContainerType(contenttype.name, self.types)


@component.adapter(IContent)
@interface.implementer(IContainerTypesConstraint)
def containers(context):
    contenttype = IContentType(context, None)
    if contenttype is not None:
        return queryUtility(IContainerTypesConstraint, contenttype.name)
