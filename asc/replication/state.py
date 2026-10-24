"""Bounded optional replication extension, preserving all existing authority."""
from ..catalog.common import CatalogError, key, content


def empty():
    return {'schema': 1, 'requests': {}}


def validate(state, doc):
    try:
        if (not isinstance(state,dict) or set(state)!={'schema','requests'} or
                type(state['schema']) is not int or state['schema']!=1 or
                not isinstance(state['requests'],dict) or len(state['requests'])>256):
            raise ValueError()
        for request,receipt in state['requests'].items():
            key(request)
            if set(receipt)!={'intent','result'} or not isinstance(receipt['result'],dict):raise ValueError()
            content(0,receipt['intent'])
        return state
    except (ValueError,KeyError,TypeError,AttributeError):
        raise CatalogError('invalid_replication_projection',409) from None
