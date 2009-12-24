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
""" IItem implementaion

$Id$
"""
from pytz import utc
from datetime import datetime
from rwproperty import getproperty, setproperty

from zope import interface
from persistent import Persistent
from zope.location import Location
from zope.dublincore.interfaces import IDCPublishing
from zope.dublincore.interfaces import ICMFDublinCore
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.app.container.interfaces import IContained

from interfaces import IItem


class Item(Location):
    """
    >>> from zope import interface, component
    >>> from zope.interface.verify import verifyClass, verifyObject

    >>> from zojax.content.type import interfaces, item

    >>> verifyClass(interfaces.IItem, item.Item)
    True

    >>> item1 = item.Item()

    >>> verifyObject(interfaces.IItem, item1)
    True

    >>> item1.title
    u''
    >>> item1.description
    u''
    >>> bool(item1)
    True

    >>> item1.title = u'title'
    >>> item1.title
    u'title'
    >>> item1.title = None
    >>> item1.title
    u''

    >>> item1.description = u'description'
    >>> item1.description
    u'description'
    >>> item1.description = None
    >>> item1.description
    u''

    >>> item2 = item.Item(u'title', u'description')
    >>> item2.title
    u'title'
    >>> item2.description
    u'description'

    >>> item2.expires
    datetime.datetime(2100, 1, 1, 0, 0, tzinfo=<UTC>)

    >>> item2.expires = datetime(2010, 1, 1, 0, 0, tzinfo=utc)
    >>> item2.expires
    datetime.datetime(2010, 1, 1, 0, 0, tzinfo=tzinfo(0))

    >>> item2.expires = None
    >>> item2.expires
    datetime.datetime(2100, 1, 1, 0, 0, tzinfo=tzinfo(0))

    >>> item2.effective
    datetime.datetime(2000, 1, 1, 0, 0, tzinfo=<UTC>)

    >>> item2.effective = datetime(2010, 1, 1, 0, 0, tzinfo=utc)
    >>> item2.effective
    datetime.datetime(2010, 1, 1, 0, 0, tzinfo=tzinfo(0))

    >>> item2.effective = datetime(1999, 1, 1, 0, 0, tzinfo=utc)
    >>> item2.effective
    datetime.datetime(2000, 1, 1, 0, 0, tzinfo=tzinfo(0))

    >>> item2.effective = None
    >>> item2.effective
    datetime.datetime(2000, 1, 1, 0, 0, tzinfo=tzinfo(0))

    """
    interface.implements(IItem, IContained, IAttributeAnnotatable)

    _default_expires = datetime(2100, 1, 1, tzinfo=utc)
    _default_effective = datetime(2000, 1, 1, tzinfo=utc)

    def __init__(self, title=u'', description=u'', **kw):
        super(Item, self).__init__(**kw)

        if title:
            self.title = title

        if description:
            self.description = description

    def __nonzero__(self):
        return True

    @getproperty
    def title(self):
        return ICMFDublinCore(self).title

    @setproperty
    def title(self, value):
        if value is None:
            value = u''
        ICMFDublinCore(self).title = unicode(value)

    @getproperty
    def description(self):
        return ICMFDublinCore(self).description

    @setproperty
    def description(self, value):
        if value is None:
            value = u''
        ICMFDublinCore(self).description = unicode(value)

    @getproperty
    def expires(self):
        return IDCPublishing(self).expires or self._default_expires

    @setproperty
    def expires(self, value):
        if value:
            IDCPublishing(self).expires = value
        else:
            IDCPublishing(self).expires = self._default_expires

    @getproperty
    def effective(self):
        return IDCPublishing(self).effective or self._default_effective

    @setproperty
    def effective(self, value):
        if value:
            if value < self._default_effective:
                IDCPublishing(self).effective = self._default_effective
            else:
                IDCPublishing(self).effective = value
        else:
            IDCPublishing(self).effective = self._default_effective


class PersistentItem(Persistent, Item):
    """ persistent item """
