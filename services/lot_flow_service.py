from copy import deepcopy
from datetime import datetime
from models.auction_state import WAITING_FOR_GROUP, LIVE_BIDDING, LOT_SOLD, PAUSED, ROUND_2, COMPLETED

class LotFlowError(ValueError):
    pass

class LotFlowService:
    def __init__(self, groups, state):
        self.groups = deepcopy(groups)
        self.state = deepcopy(state)

    def _group(self):
        gid = self.state.get('current_group_id')
        return next((g for g in self.groups if str(g.get('group_id')) == str(gid)), None)

    def _event(self, event, **extra):
        record = {'timestamp': datetime.now().strftime('%H:%M:%S'), 'event': event}
        record.update(extra)
        self.state.setdefault('history', []).append(record)

    def _clear_current(self):
        self.state['current_group_id'] = None
        self.state['current_bid'] = {'amount': 0, 'team_id': None}

    def pass_lot(self):
        if self.state.get('auction_status') != LIVE_BIDDING:
            raise LotFlowError('Lot is not currently live.')
        group = self._group()
        if not group:
            raise LotFlowError('No current auction group.')
        group['status'] = 'passed'
        group['current_bid'] = 0
        group['winner_team_id'] = None
        self._event('PASS', group_id=group['group_id'], players=list(group.get('players', [])))
        self._clear_current()
        self.state['auction_status'] = WAITING_FOR_GROUP
        return self.result('Lot passed successfully.')

    def hold_lot(self):
        if self.state.get('auction_status') != LIVE_BIDDING:
            raise LotFlowError('Lot is not currently live.')
        group = self._group()
        if not group:
            raise LotFlowError('No current auction group.')
        group['status'] = 'held'
        group['current_bid'] = 0
        group['winner_team_id'] = None
        self._event('HOLD', group_id=group['group_id'], players=list(group.get('players', [])))
        self._clear_current()
        self.state['auction_status'] = WAITING_FOR_GROUP
        return self.result('Lot held successfully.')

    def start_round_2(self):
        if not self.state.get('auction_started'):
            raise LotFlowError('Auction has not started.')
        if self.state.get('auction_finished') or self.state.get('auction_status') == COMPLETED:
            raise LotFlowError('Auction is already completed.')
        if self.state.get('auction_status') == LIVE_BIDDING:
            raise LotFlowError('Cannot start Round 2 while a lot is live.')
        if self.state.get('current_round') == 2:
            raise LotFlowError('Round 2 has already started.')
        available = [g for g in self.groups if int(g.get('round', 1)) == 2 and g.get('status') not in {'sold', 'invalid'}]
        if not available:
            raise LotFlowError('No Round 2 groups are available.')
        self.state['current_round'] = 2
        self.state['auction_status'] = ROUND_2
        self._event('ROUND_2_STARTED')
        return self.result('Round 2 started successfully.')

    def result(self, message):
        return {'success': True, 'message': message, 'data': {'groups': deepcopy(self.groups), 'auction_state': deepcopy(self.state)}}
