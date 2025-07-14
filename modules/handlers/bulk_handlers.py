from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.config import MAIN_MENU, BULK_MENU, BULK_ACTION, BULK_CONFIRM
from modules.api.bulk import BulkAPI
from modules.api.users import UserAPI
from modules.handlers.start_handler import show_main_menu

async def show_bulk_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bulk operations menu"""
    keyboard = [
        [InlineKeyboardButton("🔄 Сбросить трафик всем", callback_data="bulk_reset_all_traffic")],
        [InlineKeyboardButton("❌ Удалить неактивных", callback_data="bulk_delete_inactive")],
        [InlineKeyboardButton("❌ Удалить истекших", callback_data="bulk_delete_expired")],
        [InlineKeyboardButton("🔄 Массовое обновление", callback_data="bulk_update_all")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "🔄 *Массовые операции*\n\n"
    message += "⚠️ Внимание! Эти операции затрагивают множество пользователей одновременно.\n\n"
    message += "Выберите действие:"

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return BULK_MENU

async def handle_bulk_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bulk operations menu selection"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "bulk_reset_all_traffic":
        # Confirm reset all traffic
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, сбросить всем", callback_data="confirm_reset_all_traffic"),
                InlineKeyboardButton("❌ Отмена", callback_data="back_to_bulk")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚠️ Вы уверены, что хотите сбросить трафик ВСЕМ пользователям?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return BULK_CONFIRM

    elif data == "bulk_delete_inactive":
        # Confirm delete inactive
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить неактивных", callback_data="confirm_delete_inactive"),
                InlineKeyboardButton("❌ Отмена", callback_data="back_to_bulk")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚠️ Вы уверены, что хотите удалить ВСЕХ неактивных пользователей?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return BULK_CONFIRM

    elif data == "bulk_delete_expired":
        # Confirm delete expired
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить истекших", callback_data="confirm_delete_expired"),
                InlineKeyboardButton("❌ Отмена", callback_data="back_to_bulk")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚠️ Вы уверены, что хотите удалить ВСЕХ пользователей с истекшим сроком?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return BULK_CONFIRM

    elif data == "bulk_update_all":
        context.user_data["waiting_for"] = "bulk_update_all"
        await query.edit_message_text(
            "Введите параметры обновления в формате `field=value`.\n"
            "Можно указать несколько пар через пробел.\n"
            "Пример: `trafficLimitBytes=0 expireAt=2024-12-31`",
            parse_mode="Markdown"
        )
        return BULK_MENU

    elif data == "back_to_bulk":
        await show_bulk_menu(update, context)
        return BULK_MENU

    elif data == "back_to_main":
        await show_main_menu(update, context)
        return MAIN_MENU

    return BULK_MENU

async def handle_bulk_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bulk operation confirmation"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "confirm_reset_all_traffic":
        # Reset all users traffic
        result = await BulkAPI.bulk_reset_all_users_traffic()
        
        if result:
            message = "✅ Трафик успешно сброшен у всех пользователей."
        else:
            message = "❌ Ошибка при сбросе трафика."
        
        # Add back button
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_bulk")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return BULK_MENU

    elif data == "confirm_delete_inactive":
        # Delete all inactive users
        result = await BulkAPI.bulk_delete_users_by_status("DISABLED")
        
        if result:
            message = f"✅ Успешно удалено {result.get('deletedCount', 0)} неактивных пользователей."
        else:
            message = "❌ Ошибка при удалении пользователей."
        
        # Add back button
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_bulk")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return BULK_MENU

    elif data == "confirm_delete_expired":
        # Delete all expired users
        result = await BulkAPI.bulk_delete_users_by_status("EXPIRED")
        
        if result:
            message = f"✅ Успешно удалено {result.get('deletedCount', 0)} пользователей с истекшим сроком."
        else:
            message = "❌ Ошибка при удалении пользователей."
        
        # Add back button
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_bulk")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return BULK_MENU

    elif data == "back_to_bulk":
        await show_bulk_menu(update, context)
        return BULK_MENU

    return BULK_MENU

async def handle_bulk_update_all_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process text input for bulk update of all users"""
    text = update.message.text.strip()
    fields = {}
    for pair in text.split():
        if '=' not in pair:
            continue
        key, value = pair.split('=', 1)
        if key == 'trafficLimitBytes':
            try:
                fields[key] = int(value)
            except ValueError:
                continue
        else:
            fields[key] = value

    result = None
    if fields:
        result = await BulkAPI.bulk_update_all_users(fields)

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_bulk")]]
    if result:
        message = "✅ Массовое обновление успешно выполнено."
    else:
        message = "❌ Не удалось выполнить массовое обновление."

    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    context.user_data.pop("waiting_for", None)
    return BULK_MENU
