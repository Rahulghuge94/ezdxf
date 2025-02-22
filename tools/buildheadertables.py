#!/usr/bin/env python
# coding:utf-8
# Author:  mozman -- <mozman@gmx.at>
# Purpose: build header var tables
# Created: 12.03.2011
# Copyright (C) 2011, Manfred Moitzi
# License: MIT License
from collections import OrderedDict
from pathlib import Path
from ezdxf.lldxf.loader import load_dxf_structure

TABLEPRELUDE = """# auto-generated by buildheadertables.py - do not edit
# Copyright (C) 2019, Manfred Moitzi
# License: MIT License
from functools import partial
from ezdxf.lldxf.hdrvars import SingleValue, Point2D, Point3D, HeaderVarDef
from ezdxf.lldxf.const import DXF12, DXF2000, DXF2004, DXF2007, DXF2010, DXF2013, DXF2018
      
HEADER_VAR_MAP = {
"""
TABLEEPILOGUE = "}\n"
DXF_FILES = [
    "DXF12",
    "DXF2000",
    "DXF2004",
    "DXF2007",
    "DXF2010",
    "DXF2013",
    "DXF2018",
]
TEMPLATES = Path(r"D:\Source\dxftest\templates")


def write_table(filename, vars):
    def write_var(var):
        value = var.value
        if isinstance(value, tuple):
            if len(value) == 2:
                factory = "Point2D"
            else:
                factory = "Point3D"
        else:
            factory = "partial(SingleValue, code=%d)" % var.code
        if isinstance(value, str):
            default = "'{}'".format(value)
        else:
            default = value
        fp.write(
            "    '{v.name}': HeaderVarDef(\n"
            "        name='{v.name}',\n"
            "        code={v.code},\n"
            "        factory={f}, \n"
            "        mindxf={v.mindxf},\n"
            "        maxdxf={v.maxdxf},\n"
            "        priority={v.priority},\n"
            "        default={default}),\n".format(
                v=var, f=factory, default=default
            )
        )

    with open(filename, "wt") as fp:
        fp.write(TABLEPRELUDE)
        for var in vars:
            write_var(var)
        fp.write(TABLEEPILOGUE)


class HeaderVar:
    def __init__(self, name, code, value, priority, dxf):
        self.name = name
        self.code = code
        self.value = value
        self.priority = priority
        self.mindxf = dxf
        self.maxdxf = dxf

    def set_dxf(self, dxf):
        if self.mindxf:
            if dxf < self.mindxf:
                self.mindxf = dxf
        else:
            self.mindxf = dxf

        if self.maxdxf:
            if dxf > self.maxdxf:
                self.maxdxf = dxf
        else:
            self.maxdxf = dxf


def add_vars(header, vars, dxf):
    priority = 0
    for name_tag, value_tag in zip(header[::2], header[1::2]):
        name = name_tag.value
        code = value_tag.code
        value = value_tag.value
        h = vars.get(name, None)
        if h:
            h.set_dxf(dxf)
        else:
            vars[name] = HeaderVar(name, code, value, priority, dxf)
        priority += 100


def read(stream):
    """Open an existing drawing."""
    from ezdxf.lldxf.tagger import ascii_tags_loader, tag_compiler

    tagger = list(ascii_tags_loader(stream))
    return tag_compiler(iter(tagger))


def get_tagger(filename):
    from ezdxf.lldxf.validator import is_dxf_file
    from ezdxf.filemanagement import dxf_file_info

    if not is_dxf_file(filename):
        raise IOError("File '{}' is not a DXF file.".format(filename))

    info = dxf_file_info(filename)
    with open(
        filename, mode="rt", encoding=info.encoding, errors="ignore"
    ) as fp:
        tagger = read(fp)
    return tagger


def get_header_section(filename):
    tagger = list(get_tagger(filename))
    sections = load_dxf_structure(tagger)
    return sections.get("HEADER", [None])[
        0
    ]  # all tags in the first DXF structure entity


def main():
    header_vars = OrderedDict()
    for dxf in reversed(DXF_FILES):
        header = get_header_section(TEMPLATES / f"{dxf}.dxf")
        add_vars(header[2:], header_vars, dxf)
    write_table(
        TEMPLATES / "headervars.py",
        sorted(header_vars.values(), key=lambda v: v.priority),
    )


if __name__ == "__main__":
    main()
