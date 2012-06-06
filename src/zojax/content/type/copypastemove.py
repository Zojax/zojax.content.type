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

from zope import interface, component, event

from zope.interface import Invalid
from zope.proxy import removeAllProxies
from zope.lifecycleevent import ObjectCopiedEvent
from zope.app.container.interfaces import INameChooser
from zope.copypastemove.interfaces import IObjectMover, IObjectCopier

from zc.copy import copy

from zojax.content.type.interfaces import IContent, IRenameNotAllowed,\
    IUnremoveableContent
from zojax.content.type.constraints import checkObject


class ContentMover(object):
    """ IObjectMover for IContent """
    component.adapts(IContent)
    interface.implements(IObjectMover)

    def __init__(self, object):
        self.context = object

    def moveTo(self, target, new_name=None):
        obj = self.context
        container = obj.__parent__

        orig_name = obj.__name__
        if new_name is None:
            new_name = orig_name

        checkObject(target, new_name, obj)

        if target is container and new_name == orig_name:
            return

        chooser = INameChooser(target)
        new_name = chooser.chooseName(new_name, obj)

        target[new_name] = removeAllProxies(obj)
        del container[orig_name]
        return new_name

    def moveable(self):
        return True

    def moveableTo(self, target, name=None):
        if name is None:
            name = self.context.__name__

        try:
            checkObject(target, name, self.context)
        except Invalid:
            return False

        return True


class ContentCopier(object):
    component.adapts(IContent)
    interface.implements(IObjectCopier)

    def __init__(self, object):
        self.context = object

    def copyTo(self, target, new_name=None):
        obj = self.context
        container = obj.__parent__

        orig_name = obj.__name__
        if new_name is None:
            new_name = orig_name

        checkObject(target, new_name, obj)

        chooser = INameChooser(target)
        new_name = chooser.chooseName(new_name, obj)

        new = copy(obj)
        event.notify(ObjectCopiedEvent(new, obj))

        target[new_name] = new
        return new_name

    def copyable(self):
        return not IRenameNotAllowed.providedBy(self.context) \
            and not IUnremoveableContent.providedBy(self.context)

    def copyableTo(self, target, name=None):
        if name is None:
            name = self.context.__name__

        try:
            checkObject(target, name, self.context)
        except Invalid:
            return False

        return True
