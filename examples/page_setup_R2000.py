# Purpose: setup initial viewport for a DXF drawing
# Copyright (c) 2016-2021 Manfred Moitzi
# License: MIT License
import pathlib
import ezdxf

DIR = pathlib.Path("~/Desktop/Outbox").expanduser()
FILENAME = "page_setup_R2000.dxf"


def draw_raster(doc):
    marker = doc.blocks.new(name="MARKER")
    attribs = {"color": 2}
    marker.add_line((-1, 0), (1, 0), dxfattribs=attribs)
    marker.add_line((0, -1), (0, 1), dxfattribs=attribs)
    marker.add_circle((0, 0), 0.4, dxfattribs=attribs)

    marker.add_attdef(
        "XPOS", (0.5, -1.0), dxfattribs={"height": 0.25, "color": 4}
    )
    marker.add_attdef(
        "YPOS", (0.5, -1.5), dxfattribs={"height": 0.25, "color": 4}
    )
    modelspace = doc.modelspace()
    for x in range(10):
        for y in range(10):
            xcoord = x * 10
            ycoord = y * 10
            values = {
                "XPOS": f"x = {xcoord}",
                "YPOS": f"y = {ycoord}",
            }
            modelspace.add_auto_blockref("MARKER", (xcoord, ycoord), values)


def setup_active_viewport(doc):
    # delete '*Active' viewport configuration
    doc.viewports.delete_config("*ACTIVE")
    # the available display area in AutoCAD has the virtual lower-left
    # corner (0, 0) and the virtual upper-right corner (1, 1)

    # first viewport, uses the left half of the screen
    viewport = doc.viewports.new("*ACTIVE")
    viewport.dxf.lower_left = (0, 0)
    viewport.dxf.upper_right = (0.5, 1)

    # target point defines the origin of the DCS, this is the default value
    viewport.dxf.target = (0, 0, 0)

    # move this location (in DCS) to the center of the viewport
    viewport.dxf.center = (40, 30)

    # height of viewport in drawing units, this parameter works
    viewport.dxf.height = 15

    # aspect ratio of viewport (x/y)
    viewport.dxf.aspect_ratio = 1.0

    # second viewport, uses the right half of the screen
    viewport = doc.viewports.new("*ACTIVE")
    viewport.dxf.lower_left = (0.5, 0)
    viewport.dxf.upper_right = (1, 1)

    # target point defines the origin of the DCS
    viewport.dxf.target = (60, 20, 0)

    # move this location (in DCS, model space = 60, 20) to the center of the viewport
    viewport.dxf.center = (0, 0)

    # height of viewport in drawing units, this parameter works
    viewport.dxf.height = 15

    # aspect ratio of viewport (x/y)
    viewport.dxf.aspect_ratio = 2.0


def layout_page_setup(doc):
    name = "Layout1"
    if name in doc.layouts:
        layout = doc.layouts.get(name)
    else:
        layout = doc.layouts.new(name)

    layout.page_setup(
        size=(11, 8.5), margins=(0.5, 0.5, 0.5, 0.5), units="inch"
    )
    lower_left, upper_right = layout.get_paper_limits()
    x1, y1 = lower_left
    x2, y2 = upper_right
    center = lower_left.lerp(upper_right)
    layout.add_line((x1, center.y), (x2, center.y))  # horizontal center line
    layout.add_line((center.x, y1), (center.x, y2))  # vertical center line
    layout.add_circle((0, 0), radius=0.1)  # plot origin

    layout2 = doc.layouts.new("ezdxf scale 1-1")
    layout2.page_setup(size=(297, 210), margins=(10, 10, 10, 10), units="mm")
    layout2.add_viewport(
        # center of viewport in paper_space units
        center=(100, 100),
        # viewport size in paper_space units
        size=(50, 50),
        # model space point to show in center of viewport in WCS
        view_center_point=(60, 40),
        # how much model space area to show in viewport in drawing units
        view_height=20,
    )
    lower_left, upper_right = layout2.get_paper_limits()
    x1, y1 = lower_left
    x2, y2 = upper_right
    center = lower_left.lerp(upper_right)

    layout2.add_line((x1, center.y), (x2, center.y))  # horizontal center line
    layout2.add_line((center.x, y1), (center.x, y2))  # vertical center line
    layout2.add_circle((0, 0), radius=5)  # plot origin

    layout3 = doc.layouts.new("ezdxf scale 1-50")
    layout3.page_setup(
        size=(297, 210), margins=(10, 10, 10, 10), units="mm", scale=(1, 50)
    )
    layout3.add_viewport(
        # center of viewport in paper_space units, scale = 1:50
        center=(5000, 5000),
        # viewport size in paper_space units, scale = 1:50
        size=(5000, 2500),
        # model space point to show in center of viewport in WCS
        view_center_point=(60, 40),
        # how much model space area to show in viewport in drawing units
        view_height=20,
    )
    layout3.add_circle((0, 0), radius=250)  # plot origin

    layout4 = doc.layouts.new("ezdxf scale 1-1 with offset")
    layout4.page_setup(
        size=(297, 210),
        margins=(10, 10, 10, 10),
        units="mm",
        scale=(1, 1),
        offset=(50, 50),
    )
    lower_left, upper_right = layout4.get_paper_limits()
    x1, y1 = lower_left
    x2, y2 = upper_right
    center = lower_left.lerp(upper_right)

    layout4.add_line((x1, center.y), (x2, center.y))  # horizontal center line
    layout4.add_line((center.x, y1), (center.x, y2))  # vertical center line
    layout4.add_circle((0, 0), radius=5)  # plot origin


if __name__ == "__main__":
    doc = ezdxf.new("R2000")
    draw_raster(doc)
    setup_active_viewport(doc)
    layout_page_setup(doc)
    doc.saveas(DIR / FILENAME)
    print(f'DXF file "{FILENAME}" created.')
