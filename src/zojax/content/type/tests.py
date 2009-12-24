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
""" zojax.content tests

$Id$
"""
import unittest, doctest
from zope.app.testing import setup, placelesssetup

from zope.testing import doctest

from zope import interface, component
from zope.component.interface import provideInterface
from zope.security.management import setSecurityPolicy
from zope.securitypolicy.interfaces import IPrincipalPermissionManager
from zope.securitypolicy.principalpermission import \
    AnnotationPrincipalPermissionManager

from zojax.content.type import interfaces, order
from zojax.content.type.item import PersistentItem
from zojax.content.type.container import \
    ContentContainer, TitleBasedNameChooser, NameChooser
from zojax.content.type.contenttype import ContentType
from zojax.content.type.searchable import ContentSearchableText
from zojax.content.type.testing import setUpContents
from zojax.content.type.interfaces import ITitleBasedName


class ITestContentType(interface.Interface):
    pass

class ITestContentType1(interface.Interface):
    pass

class ITestContent1(interface.Interface):
    pass

class TestContent1(PersistentItem):
    interface.implements(ITestContent1)

    def __repr__(self):
        return '<TestContent1 "%s">'%self.__name__


class ITestContent2(interface.Interface):
    pass

class TestContent2(PersistentItem):
    interface.implements(ITestContent2)


class ITestContent3(interface.Interface):
    pass

class TestContent3(PersistentItem):
    interface.implements(ITestContent3)


class CustomContentType(ContentType):
    pass

class CustomContentType1(object):
    pass


class ITitleBasedContent(interface.Interface):
    pass

class ContentTypeWithTitleBasedName(PersistentItem):
    interface.implements(ITitleBasedContent, ITitleBasedName)

class ITestContainer(interface.Interface):
    pass

class TestContainer(ContentContainer):
    interface.implements(ITestContainer)


def setUp(test):
    placelesssetup.setUp(test)
    provideInterface("Test content types",
                     ITestContentType, interfaces.IContentTypeType)
    setUpContents()
    component.provideAdapter(
        AnnotationPrincipalPermissionManager, (interface.Interface,))
    component.provideAdapter(TitleBasedNameChooser)
    component.provideHandler(order.itemMoved)
    component.provideAdapter(order.Reordable, provides=interfaces.IOrder)
    component.provideAdapter(ContentSearchableText)
    setup.setUpTestAsModule(test, 'zojax.content.TESTS')


def tearDown(test):
    setup.tearDownTestAsModule(test)
    placelesssetup.tearDown(test)


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite(
            './README.txt',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        doctest.DocFileSuite(
            './order.txt',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        doctest.DocFileSuite(
            './container.txt',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        doctest.DocFileSuite(
            './constraints.txt',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        doctest.DocTestSuite(
            'zojax.content.type.item',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        doctest.DocTestSuite(
            'zojax.content.type.searchable',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        doctest.DocFileSuite(
            './zcml.txt',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        ))
