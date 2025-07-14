from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from modules.utils.auth import check_admin

from modules.config import MAIN_MENU, HOST_MENU
from modules.api.hosts import HostAPI
from modules.utils.formatters import format_host_details
from modules.handlers.start_handler import show_main_menu
from modules.config import WAITING_FOR_INPUT
from modules.utils.formatters import escape_markdown

async def show_hosts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show hosts menu"""
    keyboard = [
        [InlineKeyboardButton("📋 Список всех хостов", callback_data="list_hosts")],
        [InlineKeyboardButton("➕ Создать хост", callback_data="create_host")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "🌐 *Управление хостами*\n\n"
    message += "Выберите действие:"

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

@check_admin
async def handle_hosts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle hosts menu selection"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "list_hosts":
        await list_hosts(update, context)

    elif data == "create_host":
        return await start_create_host(update, context)

    elif data == "back_to_hosts":
        await show_hosts_menu(update, context)
        return HOST_MENU

    elif data == "back_to_main":
        await show_main_menu(update, context)
        return MAIN_MENU
        
    elif data.startswith("view_host_"):
        uuid = data.split("_")[2]
        await show_host_details(update, context, uuid)

    elif data.startswith("enable_host_"):
        uuid = data.split("_")[2]
        await enable_host(update, context, uuid)
        return HOST_MENU

    elif data.startswith("disable_host_"):
        uuid = data.split("_")[2]
        await disable_host(update, context, uuid)
        return HOST_MENU

    elif data.startswith("edit_host_"):
        uuid = data.split("_")[2]
        return await start_edit_host(update, context, uuid)

    elif data.startswith("edit_host_field_"):
        # edit_host_field_<field>_<uuid>
        parts = data.split("_")
        field = parts[3]
        uuid = parts[4]
        return await prompt_edit_host_field(update, context, uuid, field)

    elif data.startswith("delete_host_"):
        uuid = data.split("_")[2]
        return await confirm_delete_host(update, context, uuid)

    elif data.startswith("confirm_delete_host_"):
        uuid = data.split("_")[3]
        return await delete_host(update, context, uuid)

    return HOST_MENU

async def list_hosts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all hosts"""
    await update.callback_query.edit_message_text("🌐 Загрузка списка хостов...")

    hosts = await HostAPI.get_all_hosts()

    if not hosts:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Хосты не найдены или ошибка при получении списка.",
            reply_markup=reply_markup
        )
        return HOST_MENU

    message = f"🌐 *Хосты* ({len(hosts)}):\n\n"

    for i, host in enumerate(hosts):
        status_emoji = "🟢" if not host["isDisabled"] else "🔴"
        
        message += f"{i+1}. {status_emoji} *{host['remark']}*\n"
        message += f"   🌐 Адрес: {host['address']}:{host['port']}\n"
        message += f"   🔌 Inbound: {host['inboundUuid'][:8]}...\n\n"

    # Add action buttons
    keyboard = []
    
    for i, host in enumerate(hosts):
        keyboard.append([
            InlineKeyboardButton(f"👁️ {host['remark']}", callback_data=f"view_host_{host['uuid']}")
        ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    return HOST_MENU

async def show_host_details(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Show host details"""
    host = await HostAPI.get_host_by_uuid(uuid)
    
    if not host:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Хост не найден или ошибка при получении данных.",
            reply_markup=reply_markup
        )
        return HOST_MENU
    
    message = format_host_details(host)
    
    # Create action buttons
    keyboard = []
    
    if host["isDisabled"]:
        keyboard.append([InlineKeyboardButton("🟢 Включить", callback_data=f"enable_host_{uuid}")])
    else:
        keyboard.append([InlineKeyboardButton("🔴 Отключить", callback_data=f"disable_host_{uuid}")])
    
    keyboard.append([InlineKeyboardButton("📝 Редактировать", callback_data=f"edit_host_{uuid}")])
    keyboard.append([InlineKeyboardButton("❌ Удалить", callback_data=f"delete_host_{uuid}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад к списку", callback_data="list_hosts")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return HOST_MENU

async def enable_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Enable host"""
    await update.callback_query.answer()
    
    success = await HostAPI.enable_host(uuid)
    
    if success:
        await update.callback_query.edit_message_text("🟢 Хост успешно включен.")
    else:
        await update.callback_query.edit_message_text("❌ Не удалось включить хост.")
    
    return await show_host_details(update, context, uuid)

async def disable_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Disable host"""
    await update.callback_query.answer()
    
    success = await HostAPI.disable_host(uuid)
    
    if success:
        await update.callback_query.edit_message_text("🔴 Хост успешно отключен.")
    else:
        await update.callback_query.edit_message_text("❌ Не удалось отключить хост.")
    
    return await show_host_details(update, context, uuid)

async def start_create_host(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start host creation process"""
    context.user_data["create_host"] = {}
    context.user_data["create_host_step"] = "remark"
    context.user_data["waiting_for"] = "create_host"

    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_hosts")]]
    await update.callback_query.edit_message_text(
        "📝 Введите название хоста:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return WAITING_FOR_INPUT

async def handle_create_host_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input during host creation"""
    step = context.user_data.get("create_host_step")
    value = update.message.text.strip()

    if step == "remark":
        context.user_data["create_host"]["remark"] = value
        context.user_data["create_host_step"] = "address"
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_hosts")]]
        await update.message.reply_text(
            "🌐 Введите адрес хоста (IP или домен):",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return WAITING_FOR_INPUT

    if step == "address":
        context.user_data["create_host"]["address"] = value
        context.user_data["create_host_step"] = "port"
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_hosts")]]
        await update.message.reply_text(
            "🔢 Введите порт:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return WAITING_FOR_INPUT

    if step == "port":
        try:
            port = int(value)
        except ValueError:
            keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_hosts")]]
            await update.message.reply_text(
                "❌ Неверный формат порта. Введите число.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
            return WAITING_FOR_INPUT

        context.user_data["create_host"]["port"] = port
        context.user_data["create_host_step"] = "inboundUuid"
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_hosts")]]
        await update.message.reply_text(
            "🔌 Введите UUID inbound:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return WAITING_FOR_INPUT

    if step == "inboundUuid":
        context.user_data["create_host"]["inboundUuid"] = value
        data = context.user_data.pop("create_host")
        context.user_data.pop("create_host_step", None)
        context.user_data.pop("waiting_for", None)

        result = await HostAPI.create_host(data)

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]]
        if result:
            message = "✅ Хост успешно создан."
        else:
            message = "❌ Не удалось создать хост."

        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

        return HOST_MENU

    return WAITING_FOR_INPUT

async def start_edit_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Show field selection for host editing"""
    host = await HostAPI.get_host_by_uuid(uuid)

    if not host:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]]
        await update.callback_query.edit_message_text(
            "❌ Хост не найден.", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return HOST_MENU

    context.user_data["edit_host_uuid"] = uuid

    keyboard = [
        [InlineKeyboardButton("📝 Название", callback_data=f"edit_host_field_remark_{uuid}")],
        [InlineKeyboardButton("🔢 Порт", callback_data=f"edit_host_field_port_{uuid}")],
        [InlineKeyboardButton("🔌 Inbound UUID", callback_data=f"edit_host_field_inboundUuid_{uuid}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"view_host_{uuid}")],
    ]

    await update.callback_query.edit_message_text(
        f"📝 Редактирование хоста *{escape_markdown(host['remark'])}*\n\nВыберите поле:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return HOST_MENU

async def prompt_edit_host_field(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str, field: str):
    """Prompt for new value of a host field"""
    context.user_data["edit_host_uuid"] = uuid
    context.user_data["edit_host_field"] = field
    context.user_data["waiting_for"] = "edit_host"

    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data=f"edit_host_{uuid}")]]
    field_name = {
        "remark": "название",
        "port": "порт",
        "inboundUuid": "UUID inbound",
    }.get(field, field)

    await update.callback_query.edit_message_text(
        f"Введите новое значение для {field_name}:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return WAITING_FOR_INPUT

async def handle_edit_host_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for editing host"""
    uuid = context.user_data.get("edit_host_uuid")
    field = context.user_data.get("edit_host_field")
    value = update.message.text.strip()

    if field == "port":
        try:
            value = int(value)
        except ValueError:
            keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data=f"edit_host_{uuid}")]]
            await update.message.reply_text(
                "❌ Неверный формат порта. Введите число.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
            return WAITING_FOR_INPUT

    update_data = {field: value}
    result = await HostAPI.update_host(uuid, update_data)

    context.user_data.pop("waiting_for", None)
    context.user_data.pop("edit_host_uuid", None)
    context.user_data.pop("edit_host_field", None)

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=f"view_host_{uuid}")]]
    if result:
        message = "✅ Хост успешно обновлен."
    else:
        message = "❌ Не удалось обновить хост."

    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return HOST_MENU

async def confirm_delete_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Ask confirmation before deleting host"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=f"confirm_delete_host_{uuid}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"view_host_{uuid}")
        ]
    ]

    await update.callback_query.edit_message_text(
        "⚠️ Удалить этот хост?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
    return HOST_MENU

async def delete_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Delete host after confirmation"""
    result = await HostAPI.delete_host(uuid)
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="list_hosts")]]

    if result:
        message = "✅ Хост удален."
    else:
        message = "❌ Не удалось удалить хост."

    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return HOST_MENU
