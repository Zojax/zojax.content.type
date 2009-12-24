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
""" Use configlet as content container

$Id$
"""
from zope import interface, component, event
from zope.proxy import removeAllProxies
from zope.proxy import ProxyBase, getProxiedObject, non_overridable
from zope.proxy.decorator import DecoratorSpecificationDescriptor
from zope.security.decorator import DecoratedSecurityCheckerDescriptor
from zope.location.interfaces import ILocation
from zope.location.location import ClassAndInstanceDescr
from zope.keyreference.interfaces import IKeyReference
from zope.app.container.sample import SampleContainer
from zope.app.container.contained import uncontained
from zope.app.catalog.interfaces import INoAutoReindex

from zojax.controlpanel.configlet import Configlet
from zojax.controlpanel.interfaces import IConfiglet

from zojax.content.type.order import Reordable
from zojax.content.type.interfaces import IItem, IOrder, IContentContainer

from zope.app.container.btree import BTreeContainer


class ContentContainerConfiglet(SampleContainer, Configlet):
    interface.implements(IItem, IContentContainer, INoAutoReindex)

    def __init__(self, tests=()):
        Configlet.__init__(self, tests)

    @property
    def title(self):
        return self.__title__

    @property
    def description(self):
        return self.__description__

    @property
    def _SampleContainer__data(self):
        return self.data

    def keys(self):
        return self.data.keys()

    def items(self):
        return [(name, self[name]) for name in self]

    def get(self, key, default=None):
        item = self.data.get(key, default)

        if item is default:
            return item

        return ItemLocationProxy(removeAllProxies(item), self)

    def __contains__(self, key):
        return key in self.data

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, key):
        return ItemLocationProxy(removeAllProxies(self.data[key]), self)

    def __delitem__(self, key):
        uncontained(self[key], self, key)
        del self.data[key]


class ConfigletContainerOrder(Reordable):
    @component.adapter(ContentContainerConfiglet)

    def __init__(self, context):
        context = removeAllProxies(context)
        super(ConfigletContainerOrder, self).__init__(context.data)

        self.context = context


class ItemLocationProxy(ProxyBase):
    interface.implements(ILocation)

    __slots__ = '__parent__'
    __safe_for_unpickling__ = True

    def __new__(self, ob, container=None):
        return ProxyBase.__new__(self, ob)

    def __init__(self, ob, container=None):
        ProxyBase.__init__(self, ob)
        self.__parent__ = container

    @non_overridable
    def __reduce__(self, proto=None):
        raise TypeError("Not picklable")

    __doc__ = ClassAndInstanceDescr(
        lambda inst: getProxiedObject(inst).__doc__,
        lambda cls, __doc__ = __doc__: __doc__,
        )

    __reduce_ex__ = __reduce__
    __providedBy__ = DecoratorSpecificationDescriptor()
    __Security_checker__ = DecoratedSecurityCheckerDescriptor()


@interface.implementer(IKeyReference)
@component.adapter(ContentContainerConfiglet)
def keyReference(configlet):
    return None
