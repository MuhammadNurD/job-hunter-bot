# Job Hunter Bot

Watches [Allan Gray careers](https://www.allangray.co.za/careers/) for developer jobs that match your profile. When a new match appears, it emails you the score, CV tips, and an apply link.

`config.yaml` and `profile.json` stay on your machine. They are not committed to git.

## Windows setup

1. Install [Python 3.11+](https://www.python.org/downloads/) and tick **Add python.exe to PATH**. Close and reopen the terminal.
2. In this folder:

```bat
copy config.example.yaml config.yaml
copy profile.example.json profile.json
```

3. Put your real details in `profile.json`. Keep `config.yaml` email settings unless you need to change them.
4. Create a Gmail [App Password](https://myaccount.google.com/apppasswords) (2-Step Verification required), then run `scripts\setup-gmail.bat`.
5. Build the app:

```bat
build.bat
```

That creates `dist\JobHunterBot.exe` and a **Job Hunter Bot** shortcut on your Desktop and Start Menu.

## Run it

Double-click **Job Hunter Bot** on the Desktop, or `dist\JobHunterBot.exe`.

A blue **JH** icon appears in the hidden tray icons (`^`). Right-click it to scan now, open the log, or stop. The bot checks every 6 hours.

To start it when you log into Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-windows-task.ps1
```

Logs: `dist\data\job-hunter.log`

## Gmail folder

Emails are sent to the `to:` address in `config.yaml`. To file them in a Gmail label:

1. Set `to:` to `yourname+jobhunter@gmail.com` (keep `smtp_user` as your normal Gmail address).
2. In Gmail, create a label such as **Job Hunter**.
3. Create a filter: **To** is that `+jobhunter` address, apply the label, optionally skip the Inbox, and never send it to Spam.

Do the same in `dist\config.yaml` if you run the `.exe`.

## Optional Python commands

```bat
python -m pip install -r requirements.txt
python run.py scan --all
python run.py history
python run.py test-email
```

With no arguments, `python run.py` starts watch mode (tray icon on Windows). You can also load a LinkedIn PDF with `python run.py profile --pdf path\to\Profile.pdf --save profile.json`.

## License

MIT
