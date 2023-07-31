from abacura.plugins import action, command
from abacura_kallisti.plugins import LOKPlugin
from abacura_kallisti.atlas.room import Exit
from abacura.utils.renderables import tabulate, AbacuraPanel


class XendorianOutpost(LOKPlugin):
    """Tracks portals to/within Xendorian Outpost"""
    XENDORIAN_VNUM = '33900'
    PORTAL_AREAS = ['Midgaard City', 'Boring City']

    def __init__(self):
        super().__init__()

    @action(r"^A portal stands here, attempting to hold its shape.")
    def entrance_portal(self):
        if self.msdp.area_name in self.PORTAL_AREAS:
            self.locations.delete_location('temp.xendorian_portal')
            self.locations.add_location('temp.xendorian_portal', self.msdp.room_vnum, True)
            if self.msdp.room_vnum in self.world.rooms:
                room = self.world.rooms[self.msdp.room_vnum]
                room._exits['amorphous'] = Exit(from_vnum=room.vnum, to_vnum=self.XENDORIAN_VNUM,
                                                direction='amorphous', commands='enter amorphous', _temporary=True)
                self.debuglog(f'Xendorian Portal: [{self.msdp.room_vnum}]')

    @action(r"^A portal stands here, its horizon (\w+) ")
    def xendorian_portal(self, portal_name: str):
        if self.msdp.area_name == 'Xendorian Outpost':
            room = self.world.rooms[self.msdp.room_vnum]

            room._exits[portal_name] = Exit(from_vnum=self.msdp.room_vnum, to_vnum='?', direction=portal_name,
                                            commands=f'enter {portal_name}', _temporary=True)

            # self.world.add_temp_exit(self.msdp.room_vnum, portal_name, 'enter', '?')
            # self.session.debug(f'{portal_name} [{self.msdp.room_vnum}]')

    @command
    def xendorian(self, delete: bool = False):
        """
        List known portals in xendorian outpost

        :param delete: Delete all known xendorian portals
        """
        portals = []

        for r in self.world.rooms.values():
            if r.area_name in self.PORTAL_AREAS:
                for d, e in r.exits.items():
                    if e.temporary and e.to_vnum == self.XENDORIAN_VNUM:
                        portals.append([r, d])

            if r.area_name != 'Xendorian Outpost':
                continue

            for d, e in r.exits.items():
                if d in ['north', 'south', 'east', 'west']:
                    continue

                portals.append([r, d])

        if delete:
            for r, d in portals:
                del r.known_exits[d]
            self.output(f"[bold purple]\n{len(portals)} portals deleted")
            return

        rows = []
        for r, d in portals:
            rows.append([r.vnum, r.exits[d].to_vnum, d])

        tbl = tabulate(rows, headers=("_From", "_To", "Portal"))
        self.output(AbacuraPanel(tbl, title="Xendorian Portals"))
