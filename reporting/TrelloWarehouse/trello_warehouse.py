# -*- coding: utf-8 -*-

from trello import TrelloClient
import logging

from . import project, assignment

class TrelloWarehouse(object):
    """
    Class representing all Trello information required to do the SysDesEng reporting.
    """

    def __init__(self):
        self.logger = logging.getLogger("sysengreporting")
        self.client = TrelloClient(api_key='e5138b5715c50cc6b98b9d52e730c54d',
                                   api_secret='ca2dfff79d8a62ccdd86fbe9c4c004bd8f6d6a9345e40fce0e5af03d66209918',
                                   token='103e730b9ab62042110ca96d63dc4559ccf5d7c305297790e18651b35b3771f2',
                                   token_secret='31a508c4f0f78a7147d1dee29e652616')

        for board in self.client.list_boards():
            if board.name == 'Systems Engineering Assignments'.encode('utf-8'):
                self.logger.debug('found Systems Engineering Assignments: %s' % (board.id))
                self.syseng_assignments = board
            elif board.name == 'Private e2e Product Integration'.encode('utf-8'):
                self.logger.debug('found e2e Assignments: %s' % (board.id))
                self.e2e_board = board
            elif board.name == 'Systems Design and Engineering Projects'.encode('utf-8'):
                self.logger.debug('found Systems Design and Engineering Projects: %s' % (board.id))
                self.sysdeseng_projects = board

        self.syseng_members = self.syseng_assignments.all_members()
        self.e2e_members = self.e2e_board.all_members()

        for list in self.sysdeseng_projects.all_lists():
            if list.name == 'In Progress'.encode('utf-8'):
                self.sysdeseng_projects_cards = self.sysdeseng_projects.get_list(list.id).list_cards()

        self.projects = []
        self.assignments = dict()

    def get_projects(self):
        # check if there are some SysDesEng projects at all
        if self.sysdeseng_projects_cards is not None:
            # and for each project
            for _project in self.sysdeseng_projects_cards:
                self.logger.debug('fetching card: %s' % (_project.name))
                _project.fetch(True) # get the details from trello.com

                _p = project.Project('Systems Engineering', _project.name, _project.id  )
                self.projects.append(_p)

                self.logger.debug('new project: %s' % str(_p))

                # if the project's card has a checklist
                if _project.checklists is not None:
                    # it is per definition, the list of assignments
                    for item in _project.checklists[0].items:
                        try: # lets try to convert it into an Assignment
                            _aid = item['name'].split('/')[4]
                            _a = assignment.Assignment(_aid, _p)
                            self.assignments[_aid] = _a

                            self.logger.debug("new assignment %s" % str(_a))
                        except IndexError: # if there is no URL in there...
                            self.logger.warning("Assignment '%s' did not link back to a trello card." % (item['name']))
                            pass
        else:
            self.logger.error('sysdeseng_projects_cards was None')

        return self.projects

    def get_all_assignment_ids(self):
        """function returns a list of IDs of all assignments"""

        return self.assignments.keys()

    def get_unrelated_assignments(self):
        """function to filter out any assignment that is not related to a project"""

        _assignments = []

        all_known_assignments = self.get_all_assignment_ids()

        # lets find the SysEng 'In Progress' list and all its cards
        self.logger.debug('adding SysEng assignments')
        for list in self.syseng_assignments.all_lists():
            if list.name == 'In Progress'.encode('utf-8'):
                _assignments = _assignments + self.syseng_assignments.get_list(list.id).list_cards()

        # and append the E2E 'In Progress' list's cards
        self.logger.debug('adding E2E assignments')
        for list in self.e2e_board.all_lists():
            if list.name == 'In Progress'.encode('utf-8'):
                _assignments = _assignments + self.syseng_assignments.get_list(list.id).list_cards()

        # and get all cards aka assignments
        for assignment in _assignments:
            _aid = assignment.url.split('/')[4]
            if _aid in all_known_assignments:
                self.logger.info("we have had assignment '%s' within project '%s'" % (_aid, self.assignments[_aid].project))
            else:
                self.logger.debug('unrelated assignment: %s' % str(assignment.url.split('/')[4]))