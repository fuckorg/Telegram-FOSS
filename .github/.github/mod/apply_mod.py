"""Applies personal mod patches to the Telegram-FOSS source tree.
Run from the repository root. Fails loudly if a patch target is missing."""
import re, sys, pathlib

root = pathlib.Path(".")

def patch(path, old, new, count=1, regex=False):
    p = root / path
    s = p.read_text(encoding="utf-8")
    if regex:
        s2, n = re.subn(old, new, s, count=count)
    else:
        n = s.count(old)
        s2 = s.replace(old, new, count)
        n = min(n, count)
    if n == 0:
        sys.exit("PATCH FAILED: %s: %r not found" % (path, old[:60]))
    p.write_text(s2, encoding="utf-8")
    print("patched", path)

UC = "TMessagesProj/src/main/java/org/telegram/messenger/UserConfig.java"
# 1. Account limit: 16 slots for everyone
patch(UC, "MAX_ACCOUNT_DEFAULT_COUNT = 3;", "MAX_ACCOUNT_DEFAULT_COUNT = 16;")
patch(UC, "MAX_ACCOUNT_COUNT = 4;", "MAX_ACCOUNT_COUNT = 16;")
patch(UC, "return hasPremiumOnAccounts() ? 5 : 3;", "return 16;")

# 2. Drawer item "Logout from all accounts" (id 99)
DA = "TMessagesProj/src/main/java/org/telegram/ui/Adapters/DrawerLayoutAdapter.java"
patch(DA,
      "        items.add(new Item(13, LocaleController.getString(\"TelegramFeatures\", R.string.TelegramFeatures), helpIcon));\n",
      "        items.add(new Item(13, LocaleController.getString(\"TelegramFeatures\", R.string.TelegramFeatures), helpIcon));\n"
      "        items.add(new Item(99, \"Выйти из всех аккаунтов\", R.drawable.msg_leave));\n")

LA = "TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java"
handler = '''                } else if (id == 99) {
                    drawerLayoutContainer.closeDrawer(false);
                    AlertDialog.Builder logoutAllBuilder = new AlertDialog.Builder(LaunchActivity.this);
                    logoutAllBuilder.setTitle("Выйти из ВСЕХ аккаунтов?");
                    logoutAllBuilder.setMessage("Вы выйдете из каждого аккаунта в этом приложении. Убедитесь, что у вас есть доступ к кодам для повторного входа.");
                    logoutAllBuilder.setPositiveButton("Выйти", (dlg, which) -> {
                        for (int logoutAccount = 0; logoutAccount < UserConfig.MAX_ACCOUNT_COUNT; logoutAccount++) {
                            if (UserConfig.getInstance(logoutAccount).isClientActivated()) {
                                MessagesController.getInstance(logoutAccount).performLogout(1);
                            }
                        }
                    });
                    logoutAllBuilder.setNegativeButton("Отмена", null);
                    showAlertDialog(logoutAllBuilder);
                } else if (id == 13) {
'''
patch(LA, "                } else if (id == 13) {\n", handler)

# 3. App name
patch("TMessagesProj/src/main/res/values/strings.xml",
      '<string name="AppName">Telegram</string>', '<string name="AppName">OrganicGram</string>')

# 4. Separate package so it installs next to the official client
patch("TMessagesProj_App/build.gradle",
      "        release {\n            debuggable false\n",
      "        release {\n            applicationIdSuffix \".organicgram\"\n            debuggable false\n")

# 5. Only arm64 (modern phones) -> much faster build
patch("TMessagesProj_App/build.gradle",
      r'abiFilters "armeabi-v7a", "arm64-v8a", "x86", "x86_64"', 'abiFilters "arm64-v8a"',
      count=10, regex=True)
# 6. Native account limit must match Java
patch("TMessagesProj/jni/tgnet/Defines.h",
      "#define MAX_ACCOUNT_COUNT 5", "#define MAX_ACCOUNT_COUNT 16")
print("ALL PATCHES OK")
