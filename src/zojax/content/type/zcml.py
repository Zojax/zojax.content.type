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
""" zojax:content and zojax:reservedNames directives

$Id$
"""
import sys, logging
from zope import component
from zope.schema import TextLine
from zope.component import queryUtility
from zope.component.zcml import utility, adapter, handler
from zope.component.interface import provideInterface

from zope import interface
from zope.interface.interface import InterfaceClass

from zope.security.zcml import Permission
from zope.configuration.fields import \
     MessageID, Tokens, GlobalObject, GlobalInterface, PythonIdentifier
from zope.configuration.name import resolve

from zope.app.container.constraints import \
    IItemTypePrecondition, IContainerTypesConstraint

import zojax.content.type

from zojax.content.type.interfaces import _
from zojax.content.type.interfaces import IContent, IReservedNames
from zojax.content.type.interfaces import IActiveType, IInactiveType
from zojax.content.type.interfaces import IContentType, IContentTypeType

from zojax.content.type.contenttype import ContentType
from zojax.content.type.constraints import \
    ItemTypePrecondition, ContainerTypesConstraint

typeOf = type


class IContentTypeDirective(interface.Interface):

    schema = GlobalInterface(
        title = u'Schema',
        description = u'Content schema.',
        required = True)

    name = PythonIdentifier(
        title = u'Name',
        description = u'Content name.',
        required = True)

    title = MessageID(
        title = u'Title',
        description = u'Content title.',
        required = True)

    class_ = GlobalObject(
        title = u'Class',
        description = u'Content class',
        required = False)

    description = MessageID(
        title = u'Description',
        description = u'Content description.',
        required = False)

    permission = Permission(
        title = u'Permission',
        description = u'Specifies the adding permission.',
        required = False)

    contenttype = GlobalInterface(
        title = u'Content Type',
        description = u'Content type marker interface',
        required = False)

    ctclass = GlobalObject(
        title = u'Content Type Class',
        description = u'Custom content type implementation',
        required = False)

    type = Tokens(
        title = u'Type',
        description = u'Content type type.',
        required = False,
        value_type = GlobalInterface())

    contains = Tokens(
        title = u'Contains',
        description = u'Interface or content type name of contents '\
                            'that can be contained by this container.',
        required = False,
        value_type = TextLine())

    containers = Tokens(
        title = u'Containers',
        description = u'Containers that can contain this type of content '\
                            u'(Content name or Interface).',
        required = False,
        value_type = TextLine())

    addform = TextLine(
        title = u'Add form',
        description = u'Custom add form.',
        required = False)


class IReservedNamesDirective(interface.Interface):
    """ The name that can't be used as item name for content container """

    names = Tokens(
        title=u'The reserved name.',
        required = True,
        value_type = TextLine())

    for_ = GlobalObject(
        title = u'The interface this name is the reserved for.',
        required = False)


class IContentConstraintsDirective(interface.Interface):
    """ The name that can't be used as item name for content container """

    name = TextLine(
        title = u'Content type',
        required = True)

    contains = Tokens(
        title = u'Contains',
        description = u'Interface or content type name of contents '\
                            'that can be contained by this container.',
        required = False,
        value_type = TextLine())

    containers = Tokens(
        title = u'Containers',
        description = u'Containers that can contain this type of content '\
                            u'(Content name or Interface).',
        required = False,
        value_type = TextLine())


class ClassToTypeAdapter(object):

    def __init__(self, name):
        self.name = name

    def __call__(self, context, default=None):
        contenttype = queryUtility(IContentType, name=self.name, default=default)
        if IContentType.providedBy(contenttype):
            return contenttype.__bind__(context)


def contentHandler(_context, schema, name, title, class_=None,
                   description='', permission='zope.View',
                   contenttype=None, ctclass=None,
                   type=[], contains=(), containers=(), addform=None):

    if class_ is None:
        type = type + [IInactiveType,]

    if IInactiveType in type and IActiveType in type:
        type.remove(IActiveType)

    # make content type Active if no type is set
    if not type:
        type.append(IActiveType)

    for tp in type:
        if tp.isOrExtends(IContentType):
            raise ValueError(
                'Content type type can not extend IContentType interface.', tp)

    # check schema
    if class_ is not None and not schema.implementedBy(class_):
        raise ValueError(
            'Content class should implement content schema.', class_, schema)

    # create content type
    if ctclass is not None:
        if not IContentType.implementedBy(ctclass):
            raise ValueError('Custom content type implementation '\
                                 'should implement IContentType interface.')
        ct_factory = ctclass
    else:
        ct_factory = ContentType

    ct = ct_factory(
        name, schema, class_, title, description, permission, addform)

    # set types
    interface.alsoProvides(ct, type)

    for tp in type:
        utility(_context, tp, ct, name=name)

    # create unique interface for content type
    if contenttype is None:
        iname = name
        for ch in ('.', '-'):
            iname = iname.replace(ch, '_')

        contenttype = InterfaceClass(iname, (IContentType,),
                                     __doc__='Content Type: %s' %name,
                                     __module__='zojax.content')

        # Add the content type to the `zojax.content` module.
        setattr(zojax.content, iname, contenttype)

    # register content type as utility
    utility(_context, contenttype, ct)

    # create named utility for content type
    utility(_context, IContentType, ct, name=name)

    # adapter that return IContentType object from class instances
    adapter(_context, (ClassToTypeAdapter(name),), IContentType, (schema,))

    if class_ is not None:
        if not IContent.implementedBy(class_):
            clsifaces = list(interface.implementedBy(class_))
            clsifaces.append(IContent)
            clsifaces.extend(type)
            interface.classImplements(class_, clsifaces)

    # process constraints
    _context.action(
        discriminator = ('zojax.content:contentTypeConstraints', name),
        callable = contentTypeConstraints,
        args = (name, contains, containers, _context),
        order = 999998)

    # added custom interface to contenttype object
    _context.action(
        discriminator = ('zojax.content:contenttypeInterface', contenttype),
        callable = contenttypeInterface,
        args = (ct, contenttype))


def contenttypeInterface(ct, iface):
    provides = list(interface.directlyProvidedBy(ct))
    if iface not in provides:
        provides = [iface] + provides
        interface.directlyProvides(ct, *provides)


def contentConstraintsHandler(_context, name, contains=(), containers=()):
    _context.action(
        discriminator = ('zojax.content:constraints',
                         name, tuple(contains), tuple(containers)),
        callable = contentTypeConstraints,
        args = (name, contains, containers, _context),
        order = 999999)


def contentTypeConstraints(name, contains, containers, _context):
    sm = component.getGlobalSiteManager()

    precondition = sm.queryUtility(IItemTypePrecondition, name)
    if precondition is None:
        precondition = ItemTypePrecondition()
        sm.registerUtility(precondition, IItemTypePrecondition, name)

    # contains types
    types = precondition.types
    ifaces = precondition.ifaces

    for cname in contains:
        ct = sm.queryUtility(IContentType, cname)
        if ct is not None:
            if cname not in types:
                types.append(cname)
        else:
            try:
                iface = _context.resolve(cname)
                if iface not in ifaces:
                    ifaces.append(iface)
            except:
                if cname not in types:
                    types.append(cname)

    if not (types or ifaces):
        ifaces.append(IActiveType)

    # content containers
    if containers:
        constraint = sm.queryUtility(IContainerTypesConstraint, name)
        if constraint is None:
            constraint = ContainerTypesConstraint()
            sm.registerUtility(constraint, IContainerTypesConstraint, name)

        types = constraint.types
        ifaces = constraint.ifaces

        for cname in containers:
            ct = sm.queryUtility(IContentType, cname)
            if ct is not None:
                if cname not in types:
                    types.append(cname)
            else:
                try:
                    iface = _context.resolve(cname)
                    if iface not in ifaces:
                        ifaces.append(iface)
                except:
                    if cname not in types:
                        types.append(cname)


class ReservedNames(object):
    interface.implements(IReservedNames)

    def __init__(self, names):
        self.names = names

    def __call__(self, context):
        return self


def reservedNamesHandler(_context, names, for_):
    _context.action(
        discriminator = ('zojax.content:reservedNames', for_, tuple(names)),
        callable = reservedNames,
        args = (names, for_))


def reservedNames(names, for_):
    sm = component.getSiteManager()
    rnames = sm.adapters.lookup((for_,), IReservedNames)
    if rnames is None:
        rnames = ReservedNames(names)
        sm.registerAdapter(rnames, (for_,), IReservedNames)
    else:
        nm = list(rnames.names)
        for name in names:
            if name not in nm:
                nm.append(name)
        rnames.names = tuple(nm)
