# -*- coding: utf-8 -*-
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
""" content container

$Id$
"""
import re, string
from zope import interface, component
from zope.component import queryUtility, queryMultiAdapter
from zope.security.interfaces import Unauthorized
from zope.security.management import queryInteraction
from zope.dublincore.interfaces import IDCDescriptiveProperties
from zope.app.container.btree import BTreeContainer
from zope.app.container.contained import NameChooser as BaseNameChooser
from zope.app.container.interfaces import INameChooser

from item import Item
from interfaces import IItem, IContent, IContentContainer
from interfaces import IReservedNames, NameReserved
from interfaces import ITitleBasedName, INameChooserConfiglet


class BaseContentContainer(BTreeContainer):
    interface.implements(IItem, IContentContainer)

    def __init__(self, **kw):
        BTreeContainer.__init__(self)


class ContentContainer(Item, BaseContentContainer):
    pass


class NameChooser(BaseNameChooser):
    component.adapts(IContentContainer)

    def chooseName(self, name, object):
        namechooser = queryMultiAdapter((self.context, object), INameChooser)
        if namechooser is not None:
            return namechooser.chooseName(name, object)
        return super(NameChooser, self).chooseName(name, object)

    def checkName(self, name, object):
        names = IReservedNames(self.context, None)
        if names is not None:
            if name in names.names:
                raise NameReserved(name)

        return super(NameChooser, self).checkName(name, object)


class TitleBasedNameChooser(BaseNameChooser):
    component.adapts(IContentContainer, ITitleBasedName)

    def __init__(self, container, content):
        super(TitleBasedNameChooser, self).__init__(container)

    def chooseName(self, name, object):
        configlet = queryUtility(INameChooserConfiglet)
        if configlet is not None and configlet.short_url_enabled and not name:
            dc = IDCDescriptiveProperties(object, None)
            if dc is not None:
                name = self.getName(dc.title)

        return super(TitleBasedNameChooser, self).chooseName(name, object)

    @staticmethod
    def getName(title):
        configlet = queryUtility(INameChooserConfiglet)
        name = string.strip(
                    re.sub(
                        r'-{2,}', '-',
                        re.sub('^\w-|-\w-|-\w$', '-',
                        re.sub(r'\W', '-', string.strip(title)))), '-').lower()
        if configlet.limit_words:
            name = '-'.join(name.split('-')[0:configlet.limit_words])
        return name
