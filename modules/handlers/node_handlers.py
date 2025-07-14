from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.config import MAIN_MENU, NODE_MENU
from modules.api.nodes import NodeAPI
from datetime import datetime, timedelta
from modules.utils.formatters import format_node_details, format_bytes, escape_markdown
from modules.handlers.start_handler import show_main_menu

async def show_nodes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show nodes menu"""
    keyboard = [
        [InlineKeyboardButton("📋 Список всех серверов", callback_data="list_nodes")],
        [InlineKeyboardButton("🔄 Перезапустить все серверы", callback_data="restart_all_nodes")],
        [InlineKeyboardButton("📊 Статистика использования", callback_data="nodes_usage")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "🖥️ *Управление серверами*\n\n"
    message += "Выберите действие:"

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_nodes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle nodes menu selection"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "list_nodes":
        await list_nodes(update, context)
        return NODE_MENU

    elif data == "restart_all_nodes":
        # Confirm restart all nodes
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, перезапустить все", callback_data="confirm_restart_all"),
                InlineKeyboardButton("❌ Отмена", callback_data="back_to_nodes")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚠️ Вы уверены, что хотите перезапустить все серверы?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return NODE_MENU

    elif data == "confirm_restart_all":
        # Restart all nodes
        result = await NodeAPI.restart_all_nodes()
        
        if result and result.get("eventSent"):
            message = "✅ Команда на перезапуск всех серверов успешно отправлена."
        else:
            message = "❌ Ошибка при перезапуске серверов."
        
        # Add back button
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return NODE_MENU
        
    elif data == "nodes_usage":
        await show_nodes_usage(update, context)
        return NODE_MENU

    elif data == "back_to_nodes":
        await show_nodes_menu(update, context)
        return NODE_MENU

    elif data == "back_to_main":
        await show_main_menu(update, context)
        return MAIN_MENU
        
    elif data.startswith("view_node_"):
        uuid = data.split("_")[2]
        await show_node_details(update, context, uuid)
        return NODE_MENU
    elif data.startswith("enable_node_"):
        uuid = data.split("_")[2]
        await enable_node(update, context, uuid)
        return NODE_MENU
    elif data.startswith("disable_node_"):
        uuid = data.split("_")[2]
        await disable_node(update, context, uuid)
        return NODE_MENU
    elif data.startswith("restart_node_"):
        uuid = data.split("_")[2]
        await restart_node(update, context, uuid)
        return NODE_MENU
    elif data.startswith("node_stats_"):
        uuid = data.split("_")[2]
        await show_node_stats(update, context, uuid)
        return NODE_MENU

    return NODE_MENU

async def list_nodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all nodes"""
    await update.callback_query.edit_message_text("🖥️ Загрузка списка серверов...")

    nodes = await NodeAPI.get_all_nodes()

    if not nodes:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Серверы не найдены или ошибка при получении списка.",
            reply_markup=reply_markup
        )
        return NODE_MENU

    message = f"🖥️ *Серверы* ({len(nodes)}):\n\n"

    for i, node in enumerate(nodes):
        status_emoji = "🟢" if node["isConnected"] and not node["isDisabled"] else "🔴"
        
        message += f"{i+1}. {status_emoji} *{node['name']}*\n"
        message += f"   🌐 Адрес: {node['address']}:{node['port']}\n"
        
        if node.get("usersOnline") is not None:
            message += f"   👥 Онлайн: {node['usersOnline']}\n"
        
        if node.get("trafficLimitBytes") is not None:
            message += f"   📈 Трафик: {format_bytes(node['trafficUsedBytes'])}/{format_bytes(node['trafficLimitBytes'])}\n"
        
        message += "\n"

    # Add action buttons
    keyboard = []
    
    for i, node in enumerate(nodes):
        keyboard.append([
            InlineKeyboardButton(f"👁️ {node['name']}", callback_data=f"view_node_{node['uuid']}")
        ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    return NODE_MENU

async def show_node_details(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Show node details"""
    node = await NodeAPI.get_node_by_uuid(uuid)
    
    if not node:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Сервер не найден или ошибка при получении данных.",
            reply_markup=reply_markup
        )
        return NODE_MENU
    
    message = format_node_details(node)
    
    # Create action buttons
    keyboard = []
    
    if node["isDisabled"]:
        keyboard.append([InlineKeyboardButton("🟢 Включить", callback_data=f"enable_node_{uuid}")])
    else:
        keyboard.append([InlineKeyboardButton("🔴 Отключить", callback_data=f"disable_node_{uuid}")])
    
    keyboard.append([InlineKeyboardButton("🔄 Перезапустить", callback_data=f"restart_node_{uuid}")])
    keyboard.append([InlineKeyboardButton("📊 Статистика", callback_data=f"node_stats_{uuid}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад к списку", callback_data="list_nodes")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def show_nodes_usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show nodes usage statistics"""
    # Get realtime usage
    usage = await NodeAPI.get_nodes_realtime_usage()
    
    if not usage:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Статистика не найдена или ошибка при получении данных.",
            reply_markup=reply_markup
        )
        return NODE_MENU
    
    message = f"📊 *Статистика использования серверов*\n\n"
    
    # Sort by total bandwidth
    sorted_usage = sorted(usage, key=lambda x: x["totalBytes"], reverse=True)
    
    for i, node in enumerate(sorted_usage):
        message += f"{i+1}. *{node['nodeName']}* ({node['countryCode']})\n"
        message += f"   📥 Загрузка: {format_bytes(node['downloadBytes'])} ({format_bytes(node['downloadSpeedBps'])}/с)\n"
        message += f"   📤 Выгрузка: {format_bytes(node['uploadBytes'])} ({format_bytes(node['uploadSpeedBps'])}/с)\n"
        message += f"   📊 Всего: {format_bytes(node['totalBytes'])} ({format_bytes(node['totalSpeedBps'])}/с)\n\n"
    
    # Add action buttons
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="nodes_usage")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def enable_node(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Enable node"""
    result = await NodeAPI.enable_node(uuid)
    
    if result and result.get("success"):
        message = "✅ Сервер успешно включен."
    else:
        message = "❌ Ошибка при включении сервера."
    
    keyboard = [[InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"view_node_{uuid}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def disable_node(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Disable node"""
    result = await NodeAPI.disable_node(uuid)
    
    if result and result.get("success"):
        message = "✅ Сервер успешно отключен."
    else:
        message = "❌ Ошибка при отключении сервера."
    
    keyboard = [[InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"view_node_{uuid}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def restart_node(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Restart node"""
    result = await NodeAPI.restart_node(uuid)
    
    if result and result.get("eventSent"):
        message = "✅ Команда на перезапуск сервера успешно отправлена."
    else:
        message = "❌ Ошибка при перезапуске сервера."
    
    keyboard = [[InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"view_node_{uuid}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def show_node_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Show node statistics for the last 7 days"""
    node = await NodeAPI.get_node_by_uuid(uuid)
    end_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    usage = await NodeAPI.get_node_usage_by_range(uuid, start_date, end_date)

    if not node or not usage:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=f"view_node_{uuid}")]]
        await update.callback_query.edit_message_text(
            "❌ Статистика не найдена.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return NODE_MENU

    message = f"📊 *Статистика сервера {escape_markdown(node['name'])} за 7 дней*\n\n"

    sorted_usage = sorted(usage, key=lambda x: x.get('total', 0), reverse=True)

    for i, user in enumerate(sorted_usage[:10]):
        username = user.get('username', 'unknown')
        total = user.get('total', 0)
        message += f"{i+1}. {escape_markdown(username)} - {format_bytes(total)}\n"

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data=f"node_stats_{uuid}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"view_node_{uuid}")],
    ]

    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return NODE_MENU
