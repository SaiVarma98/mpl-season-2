from copy import deepcopy
from models.auction_state import WAITING_FOR_GROUP, LIVE_BIDDING, LOT_SOLD, PAUSED, ROUND_2, COMPLETED

class StateTransitionError(ValueError):
    pass

class AuctionStateMachine:
    def __init__(self, state):
        self.state = deepcopy(state)

    def _status(self):
        return self.state.get('auction_status', WAITING_FOR_GROUP)

    def start(self):
        if self.state.get('auction_started'):
            raise StateTransitionError('Auction has already started.')
        if self.state.get('auction_finished'):
            raise StateTransitionError('Auction is already completed.')
        self.state['auction_started'] = True
        self.state['auction_finished'] = False
        self.state['current_round'] = 1
        self.state['auction_status'] = WAITING_FOR_GROUP
        return self.state

    def select_group(self, group):
        if not self.state.get('auction_started'):
            raise StateTransitionError('Auction has not started.')
        if self.state.get('auction_finished') or self._status() == COMPLETED:
            raise StateTransitionError('Auction is already completed.')
        if self._status() == PAUSED:
            raise StateTransitionError('Auction is paused.')
        if self._status() == LIVE_BIDDING:
            raise StateTransitionError('Finish or change the current live lot first.')
        if group.get('round') != self.state.get('current_round', 1):
            raise StateTransitionError('Group does not belong to the current round.')
        if group.get('status') in {'sold', 'invalid'}:
            raise StateTransitionError('Group cannot be selected.')
        self.state['current_group_id'] = group.get('group_id')
        self.state['current_bid'] = {'amount': 0, 'team_id': None}
        self.state['auction_status'] = LIVE_BIDDING
        return self.state

    def set_bid(self, team_id, amount):
        if self._status() != LIVE_BIDDING:
            raise StateTransitionError('Bidding is not currently active.')
        self.state['current_bid'] = {'amount': int(amount), 'team_id': str(team_id)}
        return self.state
