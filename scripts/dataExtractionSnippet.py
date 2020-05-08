from dataclasses import dataclass
from tkinter import Canvas
from typing import Tuple, List
from xml.dom import minidom
from xml.etree import ElementTree
from drivebuildclient import static_vars
from generateDiagramData import Generator

@static_vars(scale=2, size=1000, origin_size=8)
def _generate_road_overlay(move_to_origin: bool = False, only_traveled_distance: bool = False) -> None:
    from tkinter import Tk, mainloop
    from lxml.etree import fromstring
    result = Generator._run_query(
        """
        SELECT ctg.author, t.environment, cta.travelleddistance
        FROM tests t
            INNER JOIN challengetestgenerator ctg ON ctg.sid = t.sid
            INNER JOIN challengetestai cta ON t.sid = cta.sid
        WHERE cta.vid = 'ego';
        """
    ).fetchall()
    env_map = {}
    for author, environment, traveled_distance in result:
        if author not in env_map:
            env_map[author] = []
        env_map[author].append((environment, traveled_distance))
    for author in env_map.keys():
        master = Tk()
        master.title("Roads of " + author)
        master.configure(background="black")
        c = Canvas(master, width=_generate_road_overlay.size, height=_generate_road_overlay.size)
        c.configure(background="white")
        c.pack()
        for environment, traveled_distance in env_map[author]:
            dbe_tree = fromstring(bytes.fromhex(environment[2:]))
            for lane_node in dbe_tree.xpath("//db:lane", namespaces=Generator.NAMESPACES):
                lane_segment_nodes = lane_node.xpath("db:laneSegment", namespaces=Generator.NAMESPACES)
                scaled_points = [_scale_point(
                    (float(l.get("x")), float(l.get("y"))),
                    _generate_road_overlay.scale
                ) for l in lane_segment_nodes]
                translated_lane, origin = _translate_lane(scaled_points, _generate_road_overlay.size, move_to_origin)

                if only_traveled_distance:
                    traveled_lane, remaining_lane = \
                        _split_lanes(translated_lane, traveled_distance)
                    _draw_lane(c, traveled_lane, "green")
                    # _draw_lane(c, remaining_lane, "red")
                else:
                    _draw_lane(c, translated_lane)
            c.create_oval(origin[0] - _generate_road_overlay.origin_size,
                          origin[1] - _generate_road_overlay.origin_size,
                          origin[0] + _generate_road_overlay.origin_size,
                          origin[1] + _generate_road_overlay.origin_size,
                          fill="red",
                          outline="red")
            axis_length = _generate_road_overlay.size / 5
            _add_coo_axis(c, axis_length)
        mainloop()
