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
from zope.security import checkPermission

from interfaces import IContentTypeChecker
from interfaces import IContentType, IContentContainer


class PermissionChecker(object):
    interface.implements(IContentTypeChecker)
    component.adapts(IContentType, IContentContainer)

    def __init__(self, contenttype, context):
        self.contenttype = contenttype
        self.context = context

    def check(self):
        contenttype = self.contenttype
        if contenttype.permission:
            return checkPermission(contenttype.permission, self.context)
        else:
            return True
