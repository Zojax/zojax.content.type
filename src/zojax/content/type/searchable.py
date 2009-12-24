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
""" ISearchableText for IContent

$Id$
"""
from zope import interface, component
from zope.index.text.interfaces import ISearchableText

from interfaces import IItem, IContent, ISearchableContent


class ContentSearchableText(object):
    """
    >>> from zojax.content.type.item import Item

    >>> class Content(Item):
    ...     interface.implements(ISearchableContent)

    >>> content = Content('Content title', 'Content description')
    >>> ISearchableText(content).getSearchableText()
    u'Content title Content description'

    >>> class Content(object):
    ...     interface.implements(ISearchableContent)

    >>> content = Content()
    >>> ISearchableText(content).getSearchableText()
    u''
    """
    component.adapts(ISearchableContent)
    interface.implements(ISearchableText)

    def __init__(self, content):
        self.content = content

    def getSearchableText(self):
        item = IItem(self.content, None)
        if item is None:
            return u''

        title = item.title.strip()
        description = item.description or u''
        return u' '.join([s for s in [title, description.strip()] if s])
