import inspect
from .. import loader, utils, main, security
import logging

from telethon.tl.types import *

logger = logging.getLogger(__name__)


@loader.tds
class HelpMod(loader.Module):
    """HELP"""
    strings = {
        "name": "Help",
        "bad_module": '<b>š I don\'t know what</b> "<code>{}</code>" <b>is!</b>',
        "single_mod_header": "<b>š Info about</b> <u>{}</u>:",
        "single_cmd": "\nš§ <code>{}{}</code> šš» ",
        "undoc_cmd": "š No docs",
        "all_header": 'š <b>{} mods available:</b>',
        "mod_tmpl": '\nš¹ <code>{}</code>',
        "first_cmd_tmpl": ": ( {}",
        "cmd_tmpl": " | {}",
        "args": "š <b>Args are incorrect</b>",
        "set_cat": "š <b>{} -> {}</b>"
    }

    async def helpcatcmd(self, message: Message) -> None:
        """<module>: <category> - Set category for module"""
        args = utils.get_args_raw(message).split(':')
        if len(args) != 2:
            await utils.answer(message, self.strings('args', message))
            return

        module_args, cat = args[0].strip(), args[1].strip()
        module = None
        for mod in self.allmodules.modules:
            if mod.strings("name", message).lower() == module_args.lower():
                module = mod

        if module is None:
            await utils.answer(message, self.strings('bad_module', message).format(module_args))
            return

        cats = self.db.get('Help', 'cats', {})
        if cat == "":
            del cats[module_args]
            cat = "default"
        else:
            cats[module_args] = cat
        self.db.set('Help', 'cats', cats)
        await utils.answer(message, self.strings('set_cat', message).format(module_args, cat))

    @loader.unrestricted
    async def helpcmd(self, message: Message) -> None:
        """[module] [-f] [-c <category>] - Show help"""
        args = utils.get_args_raw(message)
        force = False
        # print(args)
        if '-f' in args:
            args = args.replace(' -f', '').replace('-f', '')
            force = True

        category = None
        if "-c" in args:
            category = args[args.find('-c ') + 3:]
            args = args[:args.find('-c ')]

        id = message.sender_id
        prefix = utils.escape_html(
            (self.db.get(main.__name__, "command_prefix", False) or ".")[0])
        if args:
            module = None
            for mod in self.allmodules.modules:
                if mod.strings("name", message).lower() == args.lower():
                    module = mod
            if module is None:
                args = args.lower()
                args = args[1:] if args.startswith(prefix) else args
                if args in self.allmodules.commands:
                    module = self.allmodules.commands[args].__self__
                else:
                    await utils.answer(message, self.strings("bad_module", message).format(args))
                    return
            # Translate the format specification and the module separately
            try:
                name = module.strings("name", message)
            except KeyError:
                name = getattr(module, "name", "ERROR")

            reply = self.strings("single_mod_header", message).format(
                utils.escape_html(name))
            if module.__doc__:
                reply += "<i>\nā¹ļø " + \
                    utils.escape_html(inspect.getdoc(module)) + "\n</i>"
            commands = {name: func for name, func in module.commands.items() if await self.allmodules.check_security(message, func)}
            for name, fun in commands.items():
                reply += self.strings("single_cmd",
                                      message).format(prefix, name)
                if fun.__doc__:
                    reply += utils.escape_html(inspect.getdoc(fun))
                else:
                    reply += self.strings("undoc_cmd", message)
        else:
            count = 0
            for i in self.allmodules.modules:
                try:
                    if len(i.commands) != 0:
                        count += 1
                except:
                    pass
            reply = self.strings("all_header", message).format(count)
            shown_warn = False
            mods_formatted = {}
            # one_command_mods_cmds = []
            cats = {}

            for mod_name, cat in self.db.get('Help', 'cats', {}).items():
                if cat not in cats:
                    cats[cat] = []

                cats[cat].append(mod_name)

            logger.info(cats)

            for mod in self.allmodules.modules:
                if len(mod.commands) != 0:
                    tmp = ""
                    try:
                        name = mod.strings("name", message)
                    except KeyError:
                        name = getattr(mod, "name", "ERROR")
                    tmp += self.strings("mod_tmpl", message).format(name)
                    first = True
                    commands = [name for name, func in mod.commands.items() if await self.allmodules.check_security(message, func) or force]

                    # if len(commands) == 1 and (
                    #     'hide' not in cats or name not in cats['hide']
                    # ):
                    #     one_command_mods_cmds += commands
                    #     continue

                    for cmd in commands:
                        if first:
                            tmp += self.strings("first_cmd_tmpl",
                                                message).format(cmd)
                            first = False
                        else:
                            tmp += self.strings("cmd_tmpl",
                                                message).format(cmd)
                    if commands:
                        tmp += " )"
                        mods_formatted[name] = tmp

                    elif not shown_warn:
                        reply = '<i>ŠŠ¾ŠŗŠ°Š·Š°Š½Ń ŃŠ¾Š»ŃŠŗŠ¾ ŃŠµ Š¼Š¾Š“ŃŠ»Šø, Š“Š»Ń ŠŗŠ¾ŃŠ¾ŃŃŃ Š²Š°Š¼ ŃŠ²Š°ŃŠ°ŠµŃ ŃŠ°Š·ŃŠµŃŠµŠ½ŠøŠ¹ Š“Š»Ń Š²ŃŠæŠ¾Š»Š½ŠµŠ½ŠøŃ</i>\n' + reply
                        shown_warn = True
            if category is None:
                mods_remaining = mods_formatted.copy()
                for cat, mods in cats.items():
                    if cat == 'hide':
                        continue
                    tmp = ""
                    for mod in mods:
                        if mod in mods_formatted:
                            tmp += mods_formatted[mod]
                            del mods_formatted[mod]
                    if tmp != "":
                        reply += "\n\n<b><u>š¹ " + cat + "</u></b>" + tmp

                if mods_formatted:
                    reply += "\nāāāāā"

                for _, mod_formatted in mods_formatted.items():
                    if 'hide' not in cats or _ not in cats['hide']:
                        reply += mod_formatted
            else:
                tmp = ""
                for mod in cats[category]:
                    if mod in mods_formatted:
                        tmp += mods_formatted[mod]
                        del mods_formatted[mod]
                if tmp != "":
                    reply += "\n<b><u>š¹ " + category + "</u></b>" + tmp

            # reply += ("\n\n<b>1-Command Mods:</b>\n" + ' | '.join(one_command_mods_cmds)) if one_command_mods_cmds else ""

        await utils.answer(message, reply)

    async def client_ready(self, client, db) -> None:
        self.client = client
        self.is_bot = await client.is_bot()
        self.db = db
