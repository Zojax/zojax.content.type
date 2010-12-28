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
import types
from BTrees.OIBTree import OIBTree
from BTrees.IOBTree import IOBTree

from zope import interface, component
from zope.security.proxy import removeSecurityProxy
from zope.annotation.interfaces import IAnnotations
from zope.app.container.contained import notifyContainerModified
from zope.app.container.interfaces import IObjectMovedEvent

from interfaces import IOrder, IReordable, IAnnotatableOrder


class AnnotatableOrder(object):
    interface.implements(IOrder)

    ANNOTATION_KEY = 'zojax.content-containerorder'

    def __init__(self, context):
        annotations = IAnnotations(removeSecurityProxy(context))

        self.context = context
        self.annotations = annotations

        data = annotations.get(self.ANNOTATION_KEY)
        if data is None:
            self.rebuild()
        else:
            self.order, self.border = data

    def initialize(self):
        data = [IOBTree(), OIBTree()]
        self.annotations[self.ANNOTATION_KEY] = data
        self.order, self.border = data

    def generateKey(self, item):
        keys = self.order.keys()
        if keys:
            return keys[-1] + 1
        else:
            return 1

    def rebuild(self):
        self.initialize()

        for name in self.context.keys():
            self.addItem(name)

    def addItem(self, name):
        if name in self.order.values():
            return

        idx = self.generateKey(self.context[name])
        self.order[idx] = name
        self.border[name] = idx

    def removeItem(self, name):
        if name not in self.border:
            return

        idx = self.border[name]

        del self.order[idx]
        del self.border[name]

    def keys(self):
        return self.order.values()

    def __len__(self):
        return len(self.order)

    def __iter__(self):
        return iter(self.order.values())

    def __getitem__(self, key):
        if isinstance(key, types.SliceType):
            items = []
            context = self.context

            start = key.start or 0
            stop = key.stop or len(context)

            for idx in self.order.values()[start:stop]:
                items.append(context[idx])
            return items
        else:
            return self.context[key]

    def get(self, key, default=None):
        return self.context.get(key, default)

    def values(self):
        context = self.context
        return [context[key] for key in self.order.values()]

    def items(self):
        context = self.context
        return [(key, context[key]) for key in self.order.values()]

    def __contains__(self, key):
        return self.context.has_key(key)

    has_key = __contains__

    def nextKey(self, key=None):
        if key is None:
            return self.order.values()[-1]
        index = self.border[key]
        try:
            return self.order[self.order.minKey(index+1)]
        except (ValueError, KeyError):
            return self.order[index]

    def previousKey(self, key=None):
        if key is None:
            return self.order.values()[0]
        index = self.border[key]
        try:
            return self.order[self.order.maxKey(index-1)]
        except (ValueError, KeyError):
            return self.order[index]
        
    def keyPosition(self, key=None):
        if key is None:
            return 0
        return self.border[key]
    
    def getByPosition(self, position=None):
        return self.context[self.order[position]]


class Reordable(AnnotatableOrder):
    interface.implements(IReordable)
    component.adapts(IAnnotatableOrder)

    def moveUp(self, names):
        changed = False

        order = self.order
        orderKeys = order.keys()
        border = self.border
        borderKeys = border.keys()

        idxs = [border[name] for name in names if name in border]
        idxs.sort()

        if idxs and orderKeys[0] == idxs[0]:
            minKey = idxs[0]
            idxs = idxs[1:]
        else:
            minKey = orderKeys[0]-1

        for idx in idxs:
            # new position on moved item
            idx2 = order.maxKey(idx-1)
            if idx2 <= minKey:
                minKey = idx
                continue

            name1 = order[idx]
            name2 = order[idx2]
            order[idx] = name2
            order[idx2] = name1
            border[name1] = idx2
            border[name2] = idx
            changed = True

        return changed

    def moveTop(self, names):
        changed = False

        order = self.order
        orderKeys = order.keys()
        border = self.border
        borderKeys = border.keys()

        zeroIdx = orderKeys[0]

        idxs = [border[name] for name in names if name in border]
        idxs.sort()
        idxs.reverse()

        for idx in idxs:
            if zeroIdx == idx:
                continue

            name = order[idx]
            zeroIdx = zeroIdx - 1
            order[zeroIdx] = name
            border[name] = zeroIdx

            del order[idx]

            changed = True

        return changed

    def moveDown(self, names):
        changed = False

        order = self.order
        orderKeys = order.keys()
        border = self.border
        borderKeys = border.keys()

        maxKey = orderKeys[-1]+1

        idxs = [border[name] for name in names if name in border]
        idxs.sort()
        idxs.reverse()

        for idx in idxs:
            # top position
            topKey = orderKeys[-1]
            if idx >= topKey:
                maxKey = topKey
                continue

            # new position on moved item
            try:
                idx2 = order.minKey(idx+1)
            except ValueError:
                continue

            if idx2 >= maxKey:
                maxKey = idx
                continue

            name1 = order[idx]
            name2 = order[idx2]
            order[idx] = name2
            order[idx2] = name1
            border[name1] = idx2
            border[name2] = idx
            changed = True

        return changed

    def moveBottom(self, names):
        changed = False

        order = self.order
        orderKeys = order.keys()
        border = self.border
        borderKeys = border.keys()

        endIdx = orderKeys[-1]

        idxs = [border[name] for name in names if name in border]
        idxs.sort()

        for idx in idxs:
            # zero position
            if endIdx == idx:
                continue

            name = order[idx]
            endIdx = endIdx + 1
            order[endIdx] = name
            border[name] = endIdx

            del order[idx]
            changed = True

        return changed

    def updateOrder(self, order):
        if not isinstance(order, types.ListType) and \
            not isinstance(order, types.TupleType):
            raise TypeError('order must be a tuple or a list.')

        if len(order) != len(self.order):
            raise ValueError("Incompatible key set.")

        was_dict = {}
        will_be_dict = {}
        new_order = {}

        orderValues = self.order.values()

        for i in range(len(order)):
            was_dict[orderValues[i]] = 1
            will_be_dict[order[i]] = 1
            new_order[i] = order[i]

        if will_be_dict != was_dict:
            raise ValueError("Incompatible key set.")

        order = []
        keys = list(new_order.keys())
        keys.sort()
        for key in keys:
            if new_order[key] not in order:
                order.append(new_order[key])

        self.order.clear()
        self.border.clear()

        for idx in range(len(order)):
            self.order[idx] = order[idx]
            self.border[order[idx]] = idx
        notifyContainerModified(self)


@component.adapter(IObjectMovedEvent)
def itemMoved(event):
    order = IOrder(event.newParent, None)
    if order is not None:
        order.addItem(event.newName)

    order = IOrder(event.oldParent, None)
    if order is not None:
        order.removeItem(event.oldName)
