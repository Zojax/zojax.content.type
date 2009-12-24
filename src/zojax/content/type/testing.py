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
import os
from zope import component
from zope.app.testing.functional import ZCMLLayer
from zope.component.interface import provideInterface
from zope.annotation.attribute import AttributeAnnotations
from zope.lifecycleevent.interfaces import \
    IObjectModifiedEvent, IObjectCreatedEvent
from zope.dublincore.testing import setUpDublinCore
from zope.dublincore.timeannotators import ModifiedAnnotator, CreatedAnnotator
from zope.dublincore.annotatableadapter import ZDCAnnotatableAdapter
from zope.dublincore.interfaces import IDCDescriptiveProperties

from zojax.content.type import interfaces, constraints, container


def setUpContents(*args):
    setUpDublinCore()

    provideInterface("Active content types",
                     interfaces.IActiveType,
                      interfaces.IContentTypeType)
    provideInterface("Inactive content types",
                     interfaces.IInactiveType,
                     interfaces.IContentTypeType)
    provideInterface("Explictly addable content types",
                     interfaces.IExplicitlyAddable,
                     interfaces.IContentTypeType)
    component.provideAdapter(constraints.contains)
    component.provideAdapter(constraints.ctContains)
    component.provideAdapter(constraints.containers)
    component.provideAdapter(container.NameChooser)
    component.provideAdapter(container.TitleBasedNameChooser)

    component.provideAdapter(AttributeAnnotations)
    component.provideHandler(CreatedAnnotator, (IObjectCreatedEvent,))
    component.provideHandler(ModifiedAnnotator, (IObjectModifiedEvent,))
