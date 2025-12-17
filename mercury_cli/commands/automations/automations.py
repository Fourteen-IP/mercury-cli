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

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import box
from rich.text import Text

console = Console()

completer = MERCURY_CLI.completer()

completer.automations.display_meta = "Automation operations for various entities"


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
    try:
        spinner = Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}")
        )
        spinner.render()
    except ValueError:
        spinner = None
        print("Looking up alias...")

    try:
        result = MERCURY_CLI.agent().automate.find_alias(
            group_id=group_id,
            service_provider_id=service_provider_id,
            alias=alias,
        )

        if spinner:
            spinner.text = None

        if result is None:
            msg = f"✘ Alias '{alias}' not found."
            if spinner:
                spinner.update(text=msg)
            else:
                print(msg)
            return

        if result.ok:
            entity_id = getattr(
                result.payload.entity, "service_user_id", None
            ) or getattr(result.payload.entity, "user_id", None)

            msg = f"✔ Alias '{alias}' found: {entity_id}"
            if spinner:
                spinner.ok(msg)
            else:
                print(msg)
        else:
            msg = f"✘ Alias '{alias}' not found."
            if spinner:
                spinner.fail(msg)
            else:
                print(msg)

    except Exception as e:
        if spinner:
            spinner.fail("✘ Error occurred during alias lookup.")
        print(f"Error: {e}")


def _format_user_digest_output(result: AutomationResult[UserDigestResult]) -> None:
    """
    Display a beautifully formatted user digest using Rich.
    """

    STYLES = MERCURY_CLI.css()

    try:
        user_details: UserDetailsResult = result.payload.user_details
        user_info = user_details.user_info

        # Header
        _print_header()

        # Main info sections
        _print_basic_info(user_info, user_details, STYLES)
        _print_call_forwarding(user_details, STYLES)
        _print_voicemail_forwarding(user_details, STYLES)
        _print_memberships(result, STYLES)
        _print_devices(user_details, STYLES)

    except AttributeError as e:
        console.print(f"Error: Missing data field - {e}", style="red")
    except Exception as e:
        console.print(f"Error displaying user digest: {e}", style="red")


def _print_header() -> None:
    """Print the header panel."""
    STYLES = MERCURY_CLI.css()
    console.print(
        Panel(
            Text("User Digest Report", style=STYLES["header"], justify="center"),
            style=STYLES["divider"],
        )
    )


def _print_basic_info(user_info, user_details, STYLES: dict) -> None:
    """Print basic user information in a 3-column layout."""
    info_table = Table(box=None, show_header=False, padding=(0, 2), expand=True)
    info_table.add_column(style=STYLES["label"], width=18)
    info_table.add_column(style=STYLES["value"])
    info_table.add_column(style=STYLES["label"], width=18)
    info_table.add_column(style=STYLES["value"])
    info_table.add_column(style=STYLES["label"], width=18)
    info_table.add_column(style=STYLES["value"])

    # Row 1: Name, Extension, DND Status
    dnd_status = "🔇 ON" if user_details.dnd_status == "true" else "🔊 OFF"
    dnd_color = "#ff5555" if user_details.dnd_status == "true" else STYLES["success"]

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
            border_style=STYLES["divider"],
        )
    )


def _print_call_forwarding(user_details, STYLES: dict) -> None:
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
                forward_text.append(" | ", style=STYLES["separator"])
            forward_text.append(
                f"{fwd.variant.replace('_', ' ').title()}: ", style=STYLES["label"]
            )
            forward_text.append(
                fwd.forward_to_phone_number or "—", style=STYLES["success"]
            )
        console.print(
            Panel(
                forward_text,
                title="[bold #d8bbff]Active Forwards[/]",
                border_style=STYLES["divider"],
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
            selective_table.add_column("Criteria Name", style=STYLES["value"])
            selective_table.add_column("Forward To", style=STYLES["success"])
            selective_table.add_column("Time Schedule", style=STYLES["label"])
            selective_table.add_column("Call From", style=STYLES["label"])

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
                    border_style=STYLES["divider"],
                ),
            )


def _print_voicemail_forwarding(user_details, STYLES: dict) -> None:
    """Print voicemail forwarding information."""
    vm_forwards_active = [
        f for f in user_details.forwards.voicemail_forwarding if f.is_active == "true"
    ]

    if vm_forwards_active:
        forward_text = Text(justify="center")
        for i, fwd in enumerate(vm_forwards_active):
            if i > 0:
                forward_text.append(" | ", style=STYLES["separator"])
            forward_text.append(
                f"{fwd.variant.replace('voice_mail', 'vm').replace('_', ' ').title()}: ",
                style=STYLES["label"],
            )
            if fwd.is_active:
                forward_text.append("✓", style=STYLES["success"])
            else:
                forward_text.append("✗", style=STYLES["error"])
        console.print(
            Panel(
                forward_text,
                title="[bold #d8bbff]Active VM Forwards[/]",
                border_style=STYLES["divider"],
            )
        )


def _print_memberships(
    result: AutomationResult[UserDigestResult], STYLES: dict
) -> None:
    """Print membership information in a tree view."""
    membership_tree = Tree(Text("Memberships", style=STYLES["subheader"]))

    # Call Centers
    if result.payload.call_center_membership:
        cc_branch = membership_tree.add(
            Text("📞 Call Centers", style=STYLES["version"])
        )
        for cc in result.payload.call_center_membership:
            acd_state_color = (
                STYLES["success"] if cc.agent_acd_state == "Available" else "#ffaa00"
            )
            acd_available_color = (
                STYLES["success"] if cc.agent_cc_available == "true" else "#ff5555"
            )
            cc_branch.add(
                f"[{STYLES['value']}]{cc.call_center_name}[/] - "
                f"[{STYLES['label']}]{cc.call_center_id}[/] - "
                f"[{acd_state_color}]{cc.agent_acd_state}[/] - "
                f"[{acd_available_color}]Available for CC {'✓' if cc.agent_cc_available == 'true' else '✗'}[/]"
            )

    # Hunt Groups
    if result.payload.hunt_group_membership:
        hg_branch = membership_tree.add(Text("🎯 Hunt Groups", style=STYLES["version"]))
        for hg in result.payload.hunt_group_membership:
            hg_branch.add(
                f"[{STYLES['value']}]{hg.hunt_group_name}[/] - "
                f"[{STYLES['label']}]{hg.hunt_group_id}[/]"
            )

    # Pickup Groups
    if result.payload.call_pickup_group_membership:
        cpu = result.payload.call_pickup_group_membership
        pu_branch = membership_tree.add(
            Text("📫 Call Pickup Groups", style=STYLES["version"])
        )
        pu_branch.add(f"[{STYLES['value']}]{cpu.call_pickup_group_name}")

    console.print(Panel(membership_tree, border_style=STYLES["divider"]))


def _print_devices(user_details, STYLES: dict) -> None:
    """Print registered devices information."""
    if user_details.registered_devices:
        device_table = Table(
            box=box.SIMPLE, show_header=True, padding=(0, 2), expand=True
        )
        device_table.add_column("Device Name", style=STYLES["value"], min_width=20)
        device_table.add_column("Type", style=STYLES["label"], min_width=15)
        device_table.add_column("Lineport", style=STYLES["label"], min_width=15)

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
                border_style=STYLES["divider"],
            )
        )


def _format_audit_output(
    result: AutomationResult,
) -> tuple[FormattedText, Style]:
    """Format audit result with nice styling using prompt_toolkit."""

    style = Style.from_dict(MERCURY_CLI.css())

    output = []
    audit = result.payload

    # Header
    output.append(("class:header", "\n╔══════════════════════════════════════════╗\n"))
    output.append(("class:header", "║        GROUP AUDIT REPORT                ║\n"))
    output.append(("class:header", "╚══════════════════════════════════════════╝\n"))

    # Group Details Section
    if audit.group_details:
        details = audit.group_details
        output.append(("class:subheader", "\n📋 GROUP DETAILS\n"))
        output.append(("class:separator", "─" * 80 + "\n"))

        output.append(("class:label", "  Group Name:              "))
        output.append(("class:value", f"{details.group_name or 'N/A'}\n"))

        output.append(("class:label", "  Group ID:                "))
        output.append(("class:value", f"{details.group_id or 'N/A'}\n"))

        output.append(("class:label", "  Service Provider ID:     "))
        output.append(("class:value", f"{details.service_provider_id or 'N/A'}\n"))

        output.append(("class:label", "  Default Domain:          "))
        output.append(("class:value", f"{details.default_domain or 'N/A'}\n"))

        if hasattr(details, "user_count") and hasattr(details, "user_limit"):
            output.append(("class:label", "  User Count:              "))
            output.append(
                ("class:value", f"{details.user_count} / {details.user_limit}\n")
            )

        output.append(("class:label", "  Time Zone:               "))
        output.append(
            (
                "class:value",
                f"{details.time_zone_display_name or details.time_zone or 'N/A'}\n",
            )
        )

        if hasattr(details, "calling_line_id_name"):
            output.append(("class:label", "  Calling Line ID Name:    "))
            output.append(("class:value", f"{details.calling_line_id_name or 'N/A'}\n"))

        if hasattr(details, "calling_line_id_phone_number"):
            output.append(("class:label", "  Calling Line ID Phone:   "))
            output.append(
                ("class:value", f"{details.calling_line_id_phone_number or 'N/A'}\n")
            )

        if hasattr(details, "calling_line_id_display_phone_number"):
            output.append(("class:label", "  Display Phone Number:    "))
            output.append(
                (
                    "class:value",
                    f"{details.calling_line_id_display_phone_number or 'N/A'}\n",
                )
            )

    # License Breakdown - Group Services
    output.append(("class:subheader", "\n🔧 GROUP SERVICES AUTHORIZATION\n"))
    output.append(("class:separator", "─" * 80 + "\n"))
    if (
        audit.license_breakdown
        and audit.license_breakdown.group_services_authorization_table
    ):
        for service, count in sorted(
            audit.license_breakdown.group_services_authorization_table.items()
        ):
            output.append(("class:label", f"  {service:<40} "))
            output.append(("class:value", f"{count:>5}\n"))
    else:
        output.append(("class:label", "  No group services found\n"))

    # License Breakdown - Service Packs
    output.append(("class:subheader", "\n📦 SERVICE PACKS AUTHORIZATION\n"))
    output.append(("class:separator", "─" * 80 + "\n"))
    if (
        audit.license_breakdown
        and audit.license_breakdown.service_packs_authorization_table
    ):
        for pack, count in sorted(
            audit.license_breakdown.service_packs_authorization_table.items()
        ):
            output.append(("class:label", f"  {pack:<40} "))
            output.append(("class:value", f"{count:>5}\n"))
    else:
        output.append(("class:label", "  No service packs found\n"))

    # License Breakdown - User Services
    output.append(("class:subheader", "\n👤 USER SERVICES AUTHORIZATION\n"))
    output.append(("class:separator", "─" * 80 + "\n"))
    if (
        audit.license_breakdown
        and audit.license_breakdown.user_services_authorization_table
    ):
        for service, count in sorted(
            audit.license_breakdown.user_services_authorization_table.items()
        ):
            output.append(("class:label", f"  {service:<40} "))
            output.append(("class:value", f"{count:>5}\n"))
    else:
        output.append(("class:label", "  No user services found\n"))

    # Group DNs
    output.append(("class:subheader", "\n📞 GROUP DIRECTORY NUMBERS\n"))
    output.append(("class:separator", "─" * 80 + "\n"))
    if audit.group_dns:
        output.append(("class:label", "  Total DNs: "))
        output.append(("class:value", f"{audit.group_dns.total}\n"))

        if audit.group_dns.numbers:
            sorted_numbers = sorted(
                audit.group_dns.numbers,
                key=lambda x: int(x) if x.isdigit() else float("inf"),
            )
            numbers_str = ", ".join(sorted_numbers)
            max_line_length = 76
            if len(numbers_str) <= max_line_length:
                output.append(("class:value", f"  {numbers_str}\n"))
            else:
                words = numbers_str.split(", ")
                current_line = "  "
                for word in words:
                    if (
                        len(current_line) + len(word) + 2 > max_line_length
                        and current_line.strip()
                    ):
                        output.append(("class:value", current_line.rstrip() + "\n"))
                        current_line = "  " + word + ", "
                    else:
                        current_line += word + ", "
                if current_line.strip():
                    output.append(
                        ("class:value", current_line.rstrip().rstrip(",") + "\n")
                    )
        else:
            output.append(("class:label", "  No directory numbers found\n"))
    else:
        output.append(("class:label", "  Directory number information not available\n"))

    output.append(("class:divider", "\n" + "─" * 80 + "\n\n"))

    return FormattedText(output), style


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
                formatted_output, style = _format_audit_output(result)
                print_formatted_text(formatted_output, style=style)
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
