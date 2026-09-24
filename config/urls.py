from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.static import serve


def serve_spa(request):
    """
    Serves the Vue 3 SPA index.html for all non-API, non-admin frontend routes.
    """
    index_file = settings.BASE_DIR / 'frontend' / 'dist' / 'index.html'
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    return HttpResponse("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>NDBT Transport Management System</title>
            <style>
                body {
                    margin: 0;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    background: #0f172a;
                    color: #f8fafc;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    text-align: center;
                }
                .btn {
                    margin-top: 16px;
                    padding: 10px 20px;
                    border-radius: 8px;
                    background: #2563eb;
                    color: white;
                    text-decoration: none;
                    font-weight: 600;
                }
            </style>
        </head>
        <body>
            <h2>NDBT TMS Vue 3 Frontend is Initializing</h2>
            <p>Please compile the frontend with <code>npm run build</code>.</p>
            <a href="/admin/" class="btn">Access Django Admin Portal</a>
        </body>
        </html>
    """, content_type='text/html')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('register.api_urls')),

    # Serve built Vue assets in both development and production
    path('assets/<path:path>', lambda r, path: serve(r, path, document_root=settings.BASE_DIR / 'frontend' / 'dist' / 'assets')),
    path('vite.svg', lambda r: serve(r, 'vite.svg', document_root=settings.BASE_DIR / 'frontend' / 'dist')),

    # SPA fallback for Vue Router client-side routing
    re_path(r'^(?!admin/|api/|static/|media/|assets/|vite\.svg).*$', serve_spa, name='spa'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
