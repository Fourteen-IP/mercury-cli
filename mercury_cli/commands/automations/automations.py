from mercury_ocip.automate.user_digest import UserDetailsResult
from mercury_ocip.automate.user_digest import UserDigestResult
from mercury_cli.globals import MERCURY_CLI
from action_completer import Empty
from mercury_cli.utils.service_group_id_callable import (
    _get_group_id_completions,
    _get_service_provider_id_completions,
)
from mercury_ocip.automate.base_automation import AutomationResult
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import box
from rich.text import Text

console = MERCURY_CLI.console()
completer = MERCURY_CLI.completer()

completer.automations.display_meta = "Automation operations for various entities"


def _format_user_digest_output(result: AutomationResult[UserDigestResult]) -> None:
    """
    Display a beautifully formatted user digest using Rich.
    """

    try:
        user_details: UserDetailsResult = result.payload.user_details
        user_info = user_details.user_info

        # Header
        _print_header()

        # Main info sections
        _print_basic_info(user_info, user_details)
        _print_call_forwarding(user_details)
        _print_voicemail_forwarding(user_details)
        _print_memberships(result)
        _print_devices(user_details)

    except AttributeError as e:
        console.print(f"Error: Missing data field - {e}", style="red")
    except Exception as e:
        console.print(f"Error displaying user digest: {e}", style="red")


def _print_header() -> None:
    """Print the header panel."""
    console.print(
        Panel(
            Text("User Digest Report", style="header", justify="center"),
            style="divider",
        )
    )


def _print_basic_info(user_info, user_details) -> None:
    """Print basic user information in a 3-column layout."""
    info_table = Table(box=None, show_header=False, padding=(0, 2), expand=True)
    info_table.add_column(style="label", width=18)
    info_table.add_column(style="value")
    info_table.add_column(style="label", width=18)
    info_table.add_column(style="value")
    info_table.add_column(style="label", width=18)
    info_table.add_column(style="value")

    # Row 1: Name, Extension, DND Status
    dnd_status = "🔇 ON" if user_details.dnd_status == "true" else "🔊 OFF"
    dnd_color = "#ff5555" if user_details.dnd_status == "true" else "success"

    info_table.add_row(
        "Name",
        f"{user_info.first_name} {user_info.last_name}",
        "Extension",
        user_info.extension,
        "DND",
        f"[{dnd_color}]{dnd_status}[/]",
    )

    # Row 2: ID, Phone, Trunked
    info_table.add_row(
        "ID",
        user_info.user_id or "N/A",
        "Phone",
        user_info.phone_number,
        "Trunked",
        "✓" if user_info.trunk_addressing is not None else "✗",
    )

    # Row 3: Service Provider, Group, CLID
    info_table.add_row(
        "Service Provider",
        user_info.service_provider_id,
        "Group",
        user_info.group_id,
        "CLID",
        user_info.calling_line_id_phone_number,
    )

    console.print(
        Panel(
            info_table,
            title="[bold #d8bbff]Basic Info[/]",
            border_style="divider",
        )
    )


def _print_call_forwarding(user_details) -> None:
    """Print call forwarding information."""
    # Regular forwards
    forwards_active = [
        f
        for f in user_details.forwards.user_forwarding
        if f.is_active == "true" and f.variant != "Selective"
    ]

    if forwards_active:
        forward_text = Text(justify="center")
        for i, fwd in enumerate(forwards_active):
            if i > 0:
                forward_text.append(" | ", style="separator")
            forward_text.append(
                f"{fwd.variant.replace('_', ' ').title()}: ", style="label"
            )
            forward_text.append(fwd.forward_to_phone_number or "—", style="success")
        console.print(
            Panel(
                forward_text,
                title="[bold #d8bbff]Active Forwards[/]",
                border_style="divider",
            )
        )

    # Selective forwards
    selective_forwards = [
        f
        for f in user_details.forwards.user_forwarding
        if f.is_active == "true" and f.variant == "Selective" and f.selective_criteria
    ]

    if selective_forwards:
        for fwd in selective_forwards:
            selective_table = Table(box=box.SIMPLE, show_header=True, expand=True)
            selective_table.add_column("Criteria Name", style="value")
            selective_table.add_column("Forward To", style="success")
            selective_table.add_column("Time Schedule", style="label")
            selective_table.add_column("Call From", style="label")

            if fwd.selective_criteria and fwd.selective_criteria.row:
                for row in fwd.selective_criteria.row:
                    selective_table.add_row(
                        row.col[1] if len(row.col) > 1 else "N/A",
                        row.col[6] if len(row.col) > 6 else "N/A",
                        row.col[2] if len(row.col) > 2 else "N/A",
                        row.col[3] if len(row.col) > 3 else "N/A",
                    )

            console.print(
                Panel(
                    selective_table,
                    title="[bold #d8bbff]Selective Call Forwarding[/]",
                    border_style="divider",
                ),
            )


def _print_voicemail_forwarding(user_details) -> None:
    """Print voicemail forwarding information."""
    vm_forwards_active = [
        f for f in user_details.forwards.voicemail_forwarding if f.is_active == "true"
    ]

    if vm_forwards_active:
        forward_text = Text(justify="center")
        for i, fwd in enumerate(vm_forwards_active):
            if i > 0:
                forward_text.append(" | ", style="separator")
            forward_text.append(
                f"{fwd.variant.replace('voice_mail', 'vm').replace('_', ' ').title()}: ",
                style="label",
            )
            if fwd.is_active:
                forward_text.append("✓", style="success")
            else:
                forward_text.append("✗", style="error")
        console.print(
            Panel(
                forward_text,
                title="[bold #d8bbff]Active VM Forwards[/]",
                border_style="divider",
            )
        )


def _print_memberships(
    result: AutomationResult[UserDigestResult],
) -> None:
    """Print membership information in a tree view."""
    membership_tree = Tree(Text("Memberships", style="subheader"))

    # Call Centers
    if result.payload.call_center_membership:
        cc_branch = membership_tree.add(Text("📞 Call Centers", style="version"))
        for cc in result.payload.call_center_membership:
            acd_state_color = (
                "success" if cc.agent_acd_state == "Available" else "#ffaa00"
            )
            acd_available_color = (
                "success" if cc.agent_cc_available == "true" else "#ff5555"
            )
            cc_branch.add(
                f"[value]{cc.call_center_name}[/] - "
                f"[label]{cc.call_center_id}[/] - "
                f"[{acd_state_color}]{cc.agent_acd_state}[/] - "
                f"[{acd_available_color}]Available for CC {'✓' if cc.agent_cc_available == 'true' else '✗'}[/]"
            )

    # Hunt Groups
    if result.payload.hunt_group_membership:
        hg_branch = membership_tree.add(Text("🎯 Hunt Groups", style="version"))
        for hg in result.payload.hunt_group_membership:
            hg_branch.add(
                f"[value]{hg.hunt_group_name}[/] - [label]{hg.hunt_group_id}[/]"
            )

    # Pickup Groups
    if result.payload.call_pickup_group_membership:
        cpu = result.payload.call_pickup_group_membership
        pu_branch = membership_tree.add(Text("📫 Call Pickup Groups", style="version"))
        pu_branch.add(f"[value]{cpu.call_pickup_group_name}")

    console.print(Panel(membership_tree, border_style="divider"))


def _print_devices(user_details) -> None:
    """Print registered devices information."""
    if user_details.registered_devices:
        device_table = Table(
            box=box.SIMPLE, show_header=True, padding=(0, 2), expand=True
        )
        device_table.add_column("Device Name", style="value", min_width=20)
        device_table.add_column("Type", style="label", min_width=15)
        device_table.add_column("Lineport", style="label", min_width=15)

        for device in user_details.registered_devices:
            device_table.add_row(
                device.device_name or "N/A",
                device.endpoint_type or "N/A",
                device.line_port or "N/A",
            )

        console.print(
            Panel(
                device_table,
                title="[bold #d8bbff]Devices[/]",
                border_style="divider",
            )
        )


def _format_audit_output(result: AutomationResult) -> None:
    """Format and display audit result using Rich."""

    audit = result.payload

    # Header
    console.print(
        Panel(
            Text("Group Audit Report", style="header", justify="center"),
            style="divider",
        )
    )

    # Group Details Section
    if audit.group_details:
        details = audit.group_details

        details_table = Table(box=None, show_header=False, padding=(0, 2), expand=True)
        details_table.add_column(style="label", width=30)
        details_table.add_column(style="value")

        details_table.add_row("Group Name", details.group_name or "N/A")
        details_table.add_row("Group ID", details.group_id or "N/A")
        details_table.add_row(
            "Service Provider ID", details.service_provider_id or "N/A"
        )
        details_table.add_row("Default Domain", details.default_domain or "N/A")

        if hasattr(details, "user_count") and hasattr(details, "user_limit"):
            details_table.add_row(
                "User Count", f"{details.user_count} / {details.user_limit}"
            )

        details_table.add_row(
            "Time Zone", details.time_zone_display_name or details.time_zone or "N/A"
        )

        if hasattr(details, "calling_line_id_name"):
            details_table.add_row(
                "Calling Line ID Name", details.calling_line_id_name or "N/A"
            )

        if hasattr(details, "calling_line_id_phone_number"):
            details_table.add_row(
                "Calling Line ID Phone", details.calling_line_id_phone_number or "N/A"
            )

        if hasattr(details, "calling_line_id_display_phone_number"):
            details_table.add_row(
                "Display Phone Number",
                details.calling_line_id_display_phone_number or "N/A",
            )

        console.print(
            Panel(
                details_table,
                title="[bold #d8bbff]Group Details[/]",
                border_style="divider",
            )
        )

    # License Breakdown - Group Services
    if (
        audit.license_breakdown
        and audit.license_breakdown.group_services_authorization_table
    ):
        services_table = Table(box=box.SIMPLE, show_header=True, expand=True)
        services_table.add_column("Service", style="label")
        services_table.add_column("Count", style="value", justify="right")

        for service, count in sorted(
            audit.license_breakdown.group_services_authorization_table.items()
        ):
            services_table.add_row(service, str(count))

        console.print(
            Panel(
                services_table,
                title="[bold #d8bbff]Group Services Authorization[/]",
                border_style="divider",
            )
        )

    # License Breakdown - Service Packs
    if (
        audit.license_breakdown
        and audit.license_breakdown.service_packs_authorization_table
    ):
        packs_table = Table(box=box.SIMPLE, show_header=True, expand=True)
        packs_table.add_column("Service Pack", style="label")
        packs_table.add_column("Count", style="value", justify="right")

        for pack, count in sorted(
            audit.license_breakdown.service_packs_authorization_table.items()
        ):
            packs_table.add_row(pack, str(count))

        console.print(
            Panel(
                packs_table,
                title="[bold #d8bbff]Service Packs Authorization[/]",
                border_style="divider",
            )
        )

    # License Breakdown - User Services
    if (
        audit.license_breakdown
        and audit.license_breakdown.user_services_authorization_table
    ):
        user_services_table = Table(box=box.SIMPLE, show_header=True, expand=True)
        user_services_table.add_column("User Service", style="label")
        user_services_table.add_column("Count", style="value", justify="right")

        for service, count in sorted(
            audit.license_breakdown.user_services_authorization_table.items()
        ):
            user_services_table.add_row(service, str(count))

        console.print(
            Panel(
                user_services_table,
                title="[bold #d8bbff]User Services Authorization[/]",
                border_style="divider",
            )
        )

    # Group DNs
    if audit.group_dns:
        dns_text = Text()
        dns_text.append("Total DNs: ", style="label")
        dns_text.append(f"{audit.group_dns.total}\n\n", style="value")

        if audit.group_dns.numbers:
            sorted_numbers = sorted(
                audit.group_dns.numbers,
                key=lambda x: int(x) if x.isdigit() else float("inf"),
            )
            numbers_str = ", ".join(sorted_numbers)
            dns_text.append(numbers_str, style="value")
        else:
            dns_text.append("No directory numbers found", style="label")

        console.print(
            Panel(
                dns_text,
                title="[bold #d8bbff]Group Directory Numbers[/]",
                border_style="divider",
            )
        )
    else:
        console.print(
            Panel(
                Text("Directory number information not available", style="label"),
                title="[bold #d8bbff]Group Directory Numbers[/]",
                border_style="divider",
            )
        )


@completer.automations.action(
    "group_audit", display_meta="Perform a comprehensive audit of a group"
)
@completer.param(
    _get_service_provider_id_completions,
    display_meta="Service Provider ID",
    cast=str,
)
@completer.param(_get_group_id_completions, display_meta="Group ID", cast=str)
def _group_audit(service_provider_id: str, group_id: str):
    """
    Perform a comprehensive audit of a group.

    Args:
        service_provider_id: The ID of the service provider.
        group_id: The ID of the group to audit.
    """
    with console.status(
        "[cyan]Performing group audit...", spinner="dots", spinner_style="cyan"
    ) as status:
        try:
            result = MERCURY_CLI.agent().automate.audit_group(
                service_provider_id=service_provider_id,
                group_id=group_id,
            )

            if result.ok:
                status.stop()
                _format_audit_output(result)
            else:
                status.stop()
                console.print(
                    f"✘ Group audit failed for Group ID '{group_id}'.", style="red"
                )

        except Exception as e:
            status.stop()
            console.print(f"✘ {e}", style="red")


@completer.automations.action(
    "user_digest", display_meta="Perform a comprehensive audit of a user"
)
@completer.param(
    Empty,
    display_meta="User ID",
    cast=str,
)
def _user_digest(user_id: str):
    """
    Perform a comprehensive audit of a user.

    Args:
        user_id: The ID of the user to audit.
    """
    with console.status(
        "[cyan]Performing user digest...", spinner="dots", spinner_style="cyan"
    ) as status:
        try:
            result = MERCURY_CLI.agent().automate.user_digest(
                user_id=user_id,
            )

            if result.ok:
                status.stop()
                _format_user_digest_output(result)
            else:
                status.stop()
                console.print(
                    f"✘ User digest failed for User ID '{user_id}'.", style="red"
                )

        except Exception as e:
            status.stop()
            console.print(f"✘ {e}", style="red")


@completer.automations.action(
    "find_alias", display_meta="Find the given entity behind an alias"
)
@completer.param(
    _get_service_provider_id_completions,
    display_meta="Service Provider ID",
    cast=str,
)
@completer.param(_get_group_id_completions, display_meta="Group ID", cast=str)
@completer.param(Empty, display="alias", display_meta="Alias Number", cast=str)
def _find_alias(service_provider_id: str, group_id: str, alias: str):
    """
    Find the entity behind a given alias.

    Args:
        alias_name: The name of the alias to look up.
    """
    with console.status(
        "[cyan]Looking up alias...", spinner="dots", spinner_style="cyan"
    ) as status:
        try:
            result = MERCURY_CLI.agent().automate.find_alias(
                group_id=group_id,
                service_provider_id=service_provider_id,
                alias=alias,
            )

            status.stop()

            if result is None:
                console.print(f"✘ Alias '{alias}' not found.", style="red")
                return

            if result.ok:
                entity_id = getattr(
                    result.payload.entity, "service_user_id", None
                ) or getattr(result.payload.entity, "user_id", None)

                console.print(f"✔ Alias '{alias}' found: {entity_id}", style="green")
            else:
                console.print(f"✘ Alias '{alias}' not found.", style="red")

        except Exception as e:
            status.stop()
            console.print(f"✘ {e}", style="red")
