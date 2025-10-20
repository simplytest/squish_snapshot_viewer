import webview
from webview.menu import Menu, MenuAction

def handle_menu_click(window, item):
    if item.uid == 'exit_action':
        window.destroy()

def main():
    initial_html = "<h1>Hello World</h1><p>This is a simple pywebview app.</p>"
    
    window = webview.create_window(
        'Simple Pywebview App',
        html=initial_html,
        width=800,
        height=600
    )

    menu_items = [
        Menu('File', [
            MenuAction('Exit', lambda: handle_menu_click(window, MenuAction('', None, 'exit_action')))
        ])
    ]

    webview.start(menu=menu_items)

if __name__ == '__main__':
    main()
