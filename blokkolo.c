#include <string.h>
#include <webkit/webkit-web-process-extension.h>

static GHashTable *tiltott, *engedett;
static char *ut_tiltott, *ut_engedett;

static GHashTable *beolvas(const char *ut) {
    GHashTable *h = g_hash_table_new_full(g_str_hash, g_str_equal, g_free, NULL);
    char *adat = NULL;
    if (g_file_get_contents(ut, &adat, NULL, NULL)) {
        char **sorok = g_strsplit(adat, "\n", -1);
        for (char **s = sorok; *s; s++)
            if (**s)
                g_hash_table_add(h, g_strdup(*s));
        g_strfreev(sorok);
        g_free(adat);
    }
    return h;
}

static void betolt(void) {
    g_clear_pointer(&tiltott, g_hash_table_unref);
    g_clear_pointer(&engedett, g_hash_table_unref);
    tiltott = beolvas(ut_tiltott);
    engedett = beolvas(ut_engedett);
}

static char *gazda(const char *uri) {
    if (!uri)
        return NULL;
    GUri *u = g_uri_parse(uri, G_URI_FLAGS_NONE, NULL);
    if (!u)
        return NULL;
    char *h = g_uri_get_host(u) ? g_ascii_strdown(g_uri_get_host(u), -1) : NULL;
    g_uri_unref(u);
    return h;
}

static const char *talal(const char *host) {
    for (const char *p = host; p && strchr(p, '.'); p = strchr(p, '.') + 1)
        if (g_hash_table_contains(tiltott, p))
            return p;
    return NULL;
}

static gboolean keres(WebKitWebPage *lap, WebKitURIRequest *kerelem, WebKitURIResponse *atiranyitas, gpointer _) {
    char *host = gazda(webkit_uri_request_get_uri(kerelem));
    char *lap_host = gazda(webkit_web_page_get_uri(lap));
    const char *d = NULL;
    if (host && *host && !(lap_host && (!strcmp(host, lap_host) || g_hash_table_contains(engedett, lap_host))))
        d = talal(host);
    if (d)
        webkit_web_page_send_message_to_view(lap, webkit_user_message_new("blokk", g_variant_new_string(d)), NULL, NULL, NULL);
    else {
        SoupMessageHeaders *fej = webkit_uri_request_get_http_headers(kerelem);
        if (fej)
            soup_message_headers_replace(fej, "Sec-GPC", "1");
    }
    g_free(host);
    g_free(lap_host);
    return d != NULL;
}

static gboolean uzenet(WebKitWebPage *lap, WebKitUserMessage *u, gpointer _) {
    if (g_strcmp0(webkit_user_message_get_name(u), "frissit"))
        return FALSE;
    betolt();
    return TRUE;
}

static void uj_lap(WebKitWebProcessExtension *_, WebKitWebPage *lap, gpointer __) {
    g_signal_connect(lap, "send-request", G_CALLBACK(keres), NULL);
    g_signal_connect(lap, "user-message-received", G_CALLBACK(uzenet), NULL);
}

G_MODULE_EXPORT void webkit_web_process_extension_initialize_with_user_data(WebKitWebProcessExtension *kit, const GVariant *adat) {
    g_variant_get((GVariant *)adat, "(ss)", &ut_tiltott, &ut_engedett);
    betolt();
    g_signal_connect(kit, "page-created", G_CALLBACK(uj_lap), NULL);
}
