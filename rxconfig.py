import reflex as rx

config = rx.Config(
    app_name="resultdashboard_reflex",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)