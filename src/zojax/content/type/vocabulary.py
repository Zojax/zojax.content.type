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
from zope import interface
from zope.component import getUtilitiesFor
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from zojax.content.type.interfaces import IContentType, IPortalType


class AddableContent(object):
    interface.implements(IVocabularyFactory)

    def __call__(self, context):
        contenttype = IContentType(context, None)
        if contenttype is None:
            return SimpleVocabulary([])

        result = []
        for ptype in contenttype.listContainedTypes():
            result.append((ptype.title, ptype.name))

        result.sort()
        return SimpleVocabulary([
                SimpleTerm(name, name, title) for title, name in result])


class PortalContent(object):
    interface.implements(IVocabularyFactory)

    def __call__(self, context):
        result = []
        for name, ptype in getUtilitiesFor(IPortalType):
            result.append((ptype.title, ptype.name))

        result.sort()
        return SimpleVocabulary([
                SimpleTerm(name, name, title) for title, name in result])
