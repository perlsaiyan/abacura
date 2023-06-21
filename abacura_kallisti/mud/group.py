from dataclasses import dataclass
from typing import List, Dict


@dataclass
class GroupMember:
    name: str
    cls: str
    level: int
    position: str
    flags: str
    hp: int
    mp: int
    sp: int
    is_leader: bool
    is_subleader: bool
    with_leader: bool
    with_you: bool


class Group:
    def __init__(self):
        self.members: List[GroupMember] = []

    def update_members_from_msdp(self, member_list: List[Dict[str, str]]):
        self.members = []
        for m in member_list:
            gm = GroupMember(name=m['name'], cls=m['class'], level=int(m['level']), position=m['position'],
                             flags=m['flags'], hp=int(m['health']), mp=int(m['mana']), sp=int(m['stamina']),
                             is_leader=bool(m['is_leader']), is_subleader=bool(m['is_subleader']),
                             with_leader=bool(m['with_leader']), with_you=bool(m['with_you']))
            self.members.append(gm)

    def get_leaders(self) -> List[GroupMember]:
        return [m for m in self.members if m.is_leader or m.is_subleader]

    def get_pcs(self) -> List[GroupMember]:
        return [m for m in self.members if m.cls not in ('MOB', 'NPC') and m.flags.find('NPC') == -1]

    def get_num_pcs_in_group(self) -> int:
        return len(self.get_pcs())

    def get_num_pcs_with_you(self) -> int:
        return len([m for m in self.get_pcs() if m.with_you])

    def get_members_with_you(self) -> List[GroupMember]:
        return [m for m in self.members if m.with_you]

    def get_num_with_you(self) -> int:
        return len(self.get_members_with_you())

    def get_num_followers_with_you(self) -> int:
        followers = [m for m in self.members if m.with_you and (m.cls == 'MOB' or m.flags.find('NPC') >= 0)]
        return len(followers)
