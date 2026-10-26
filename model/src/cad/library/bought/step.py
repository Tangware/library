from collections.abc import Iterator
from pathlib import Path

from build123d import Location, Shape, Solid
from OCP.collections import Sequence_TDF_Label
from OCP.Quantity import Quantity_ColorRGBA, Quantity_TOC_sRGB
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label
from OCP.TDocStd import TDocStd_Document
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS_Shape
from OCP.XCAFDoc import (
    XCAFDoc_ColorCurv,
    XCAFDoc_ColorGen,
    XCAFDoc_ColorSurf,
    XCAFDoc_ColorTool,
    XCAFDoc_DocumentTool,
    XCAFDoc_ShapeTool,
)

from cad.library.bought.catalogue import Rgb

type Look = tuple[Rgb | None, ...]
type Named = tuple[Solid, Look, str]
KINDS = (XCAFDoc_ColorSurf, XCAFDoc_ColorGen, XCAFDoc_ColorCurv)


def _rgb(found: Quantity_ColorRGBA) -> Rgb:
    return found.GetRGB().Values(Quantity_TOC_sRGB)


def label_name(label: TDF_Label) -> str:
    found = TDataStd_Name()
    return found.Get().ToExtString() if label.FindAttribute(TDataStd_Name.GetID_s(), found) else ""


def coloured_step(path: Path) -> list[Named]:
    document = TDocStd_Document(TCollection_ExtendedString("XCAF"))
    reader = STEPCAFControl_Reader()
    reader.SetColorMode(True)
    reader.SetNameMode(True)
    reader.ReadFile(str(path))
    reader.Transfer(document)
    shapes = XCAFDoc_DocumentTool.ShapeTool_s(document.Main())
    colours = XCAFDoc_DocumentTool.ColorTool_s(document.Main())

    def shape_colour(shape: TopoDS_Shape) -> Rgb | None:
        found = Quantity_ColorRGBA()
        return _rgb(found) if any(colours.GetColor(shape, k, found) for k in KINDS) else None

    def label_colour(label: TDF_Label) -> Rgb | None:
        found = Quantity_ColorRGBA()
        painted = any(XCAFDoc_ColorTool.GetColor_s(label, k, found) for k in KINDS)
        return _rgb(found) if painted else None

    def walk(
        labels: Sequence_TDF_Label, placed: TopLoc_Location, inherited: Rgb | None, trail: str
    ) -> Iterator[Named]:
        for index in range(1, labels.Length() + 1):
            label = labels.Value(index)
            referred = label
            if XCAFDoc_ShapeTool.IsReference_s(label):
                referred = TDF_Label()
                XCAFDoc_ShapeTool.GetReferredShape_s(label, referred)
            painted = label_colour(label) or label_colour(referred) or inherited
            location = placed * XCAFDoc_ShapeTool.GetLocation_s(label)
            named = f"{trail}/{label_name(label)}:{label_name(referred)}"
            if XCAFDoc_ShapeTool.IsAssembly_s(referred):
                parts = Sequence_TDF_Label()
                XCAFDoc_ShapeTool.GetComponents_s(referred, parts)
                yield from walk(parts, location, painted, named)
                continue
            for solid in Shape.cast(XCAFDoc_ShapeTool.GetShape_s(referred)).solids():
                whole = shape_colour(solid.wrapped) or painted
                look = tuple(shape_colour(face.wrapped) or whole for face in solid.faces())
                yield solid.moved(Location(location)), look, named

    roots = Sequence_TDF_Label()
    shapes.GetFreeShapes(roots)
    return list(walk(roots, TopLoc_Location(), None, ""))
