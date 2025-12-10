from typing import Iterable, Optional
from action_completer.types import ActionParam, Action
from action_completer.utils import get_fragments
from mercury_ocip.commands.commands import (
    GroupGetListInServiceProviderPagedSortedListRequest,
    GroupGetListInServiceProviderPagedSortedListResponse,
    ServiceProviderGetListRequest,
    ServiceProviderGetListResponse,
)
from mercury_cli.globals import MERCURY_CLI


def _get_group_id_completions(
    action: Action, param: Optional[ActionParam] = None, value: str = ""
) -> Iterable[str]:
    """
    Provides dynamic completions for the 'group_id' parameter based on the selected 'service_provider_id'.

    Args:
        action (Action): The action for which completions are being provided.
        param (ActionParam): The parameter for which completions are being provided.
        value (str): The current input value for the parameter.

    Returns:
        Iterable[str]: A list of possible completions for the 'group_id' parameter.
    """

    buffer_text = MERCURY_CLI.session().default_buffer.document.text
    fragments = get_fragments(buffer_text)

    group_param_index = next(
        (
            i
            for i, p in enumerate(action.params)
            if p.source == _get_group_id_completions
        ),
        -1,
    )
    sp_param_index = next(
        (
            i
            for i, p in enumerate(action.params)
            if p.source == _get_service_provider_id_completions
        ),
        -1,
    )

    if group_param_index == -1 or sp_param_index == -1:
        return []

    offset = group_param_index - sp_param_index
    fragment_index = len(fragments) - 1 - offset

    if 0 <= fragment_index < len(fragments):
        service_provider_id = fragments[fragment_index]
    else:
        service_provider_id = None

    if not service_provider_id:
        return []

    try:
        client = MERCURY_CLI.client()
        groups: GroupGetListInServiceProviderPagedSortedListResponse = client.command(
            GroupGetListInServiceProviderPagedSortedListRequest(
                service_provider_id=service_provider_id
            )
        )
        group_ids = [g.get("group_id", "") for g in getattr(groups, "group_table", [])]
        if value:
            group_ids = [gid for gid in group_ids if str(gid).startswith(value)]
        return group_ids
    except Exception:
        return []


def _get_service_provider_id_completions(
    action: Action, param: Optional[ActionParam] = None, value: str = ""
) -> Iterable[str]:
    """
    Provides dynamic completions for the 'service_provider_id' parameter.

    Args:
        action (Action): The action for which completions are being provided.
        param (ActionParam): The parameter for which completions are being provided.
        value (str): The current input value for the parameter.

    Returns:
        Iterable[str]: A list of possible completions for the 'service_provider_id' parameter.
    """
    service_providers: Optional[ServiceProviderGetListResponse] = None
    try:
        client = MERCURY_CLI.client()
        service_providers = client.command(ServiceProviderGetListRequest())
    except Exception:
        return []

    try:
        sp_ids = [
            sp.get("service_provider_id", "")
            for sp in getattr(service_providers, "service_provider_table", [])
        ]
        if value:
            sp_ids = [sid for sid in sp_ids if str(sid).startswith(value)]
        return sp_ids
    except Exception:
        return []
