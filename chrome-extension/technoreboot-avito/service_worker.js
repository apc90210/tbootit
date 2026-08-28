// Technoreboot Avito Extension Service Worker (Manifest V3 v0.1.8)

const BRIDGE_BASE_URL = "http://localhost:8011/admin-api/avito-extension";

async function getStoredToken() {
    return new Promise(resolve => {
        chrome.storage.local.get(["extension_token"], result => {
            resolve(result.extension_token || null);
        });
    });
}

async function setStoredToken(token) {
    return new Promise(resolve => {
        chrome.storage.local.set({ extension_token: token }, () => {
            resolve();
        });
    });
}

async function parseJsonResponseSafely(res) {
    const contentType = res.headers.get("content-type") || "";
    let text = "";
    try {
        text = await res.text();
    } catch (e) {
        text = "";
    }

    let data = null;
    if (text && (contentType.includes("application/json") || text.trim().startsWith("{") || text.trim().startsWith("["))) {
        try {
            data = JSON.parse(text);
        } catch (e) {
            data = null;
        }
    }

    if (res.ok) {
        if (data) {
            return { ok: true, status: res.status, data: data };
        } else {
            return { ok: false, status: res.status, error: "Некорректный (не-JSON) ответ сервера при успешном HTTP статусе.", text: text };
        }
    } else {
        // Non-2xx HTTP status
        if (data) {
            let errMsg = null;
            if (typeof data.detail === "string") {
                errMsg = data.detail;
            } else if (data.detail && typeof data.detail === "object") {
                errMsg = data.detail.message || data.detail.error || JSON.stringify(data.detail);
            } else if (data.message) {
                errMsg = data.message;
            } else if (data.error) {
                errMsg = data.error;
            }
            if (errMsg) {
                return { ok: false, status: res.status, error: `Ошибка сервера ${res.status}: ${errMsg}`, data: data };
            }
        }
        const safeText = text ? text.slice(0, 150).trim() : "Internal Server Error";
        return { ok: false, status: res.status, error: `Ошибка сервера ${res.status}: ${safeText}` };
    }
}

async function checkBridgeStatus() {
    try {
        const token = await getStoredToken();
        const res = await fetch(`${BRIDGE_BASE_URL}/status`, {
            headers: token ? { "X-Extension-Token": token } : {}
        });
        const parsed = await parseJsonResponseSafely(res);
        if (parsed.ok) {
            const data = parsed.data;
            const isPaired = data.paired === true && Boolean(token);
            if (token && !data.paired) {
                await new Promise(r => chrome.storage.local.remove(["extension_token"], r));
            }
            return {
                online: true,
                paired: isPaired,
                has_token: Boolean(token),
                token_valid: data.token_valid === true,
                version: data.version || "0.1.9"
            };
        }
        return { online: false, error: parsed.error };
    } catch (e) {
        return { online: false, error: e.message };
    }
}

async function pairExtension(code) {
    try {
        const res = await fetch(`${BRIDGE_BASE_URL}/pairing/pair`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pair_code: code })
        });
        const parsed = await parseJsonResponseSafely(res);
        if (parsed.ok && parsed.data.status === "paired" && parsed.data.extension_token) {
            await setStoredToken(parsed.data.extension_token);
            return { success: true, message: "Расширение успешно привязано к Техноребут!" };
        }
        return { success: false, message: parsed.error || (parsed.data && parsed.data.detail) || "Неверный код подключения." };
    } catch (e) {
        return { success: false, message: `Ошибка связи с сервером: ${e.message}` };
    }
}

async function sendListingPayload(payload) {
    const token = await getStoredToken();
    if (!token) {
        return { success: false, message: "Расширение не привязано к Техноребут. Введите код подключения." };
    }
    try {
        const res = await fetch(`${BRIDGE_BASE_URL}/listing`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Extension-Token": token
            },
            body: JSON.stringify(payload)
        });
        const parsed = await parseJsonResponseSafely(res);
        if (parsed.ok) {
            const data = parsed.data;
            if ((data.status === "success" || data.status === "imported" || data.status === "partial" || data.status === "created" || data.status === "updated") && data.product_id != null) {
                return {
                    success: true,
                    status: data.status,
                    product_id: data.product_id,
                    photos_imported: data.photos_imported || (data.details && data.details.photos_imported) || 0,
                    result: data.result,
                    message: data.message || `Объявление ${data.external_item_id} обработано!`,
                    details: data
                };
            }
            const errMsg = data.message || "Не удалось импортировать объявление.";
            return { success: false, product_id: null, message: errMsg, details: data };
        } else {
            return { success: false, product_id: null, message: parsed.error, details: parsed.data };
        }
    } catch (e) {
        return { success: false, product_id: null, message: `Ошибка сети/подключения: ${e.message}` };
    }
}

async function sendMyListingsPayload(payload) {
    const token = await getStoredToken();
    if (!token) {
        return { success: false, message: "Расширение не привязано к Техноребут." };
    }
    try {
        const res = await fetch(`${BRIDGE_BASE_URL}/my-listings`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Extension-Token": token
            },
            body: JSON.stringify(payload)
        });
        const parsed = await parseJsonResponseSafely(res);
        if (parsed.ok) {
            const data = parsed.data;
            return { success: true, message: `Список объявлений получен (найдено: ${data.count || 0}).`, details: data };
        }
        return { success: false, message: parsed.error };
    } catch (e) {
        return { success: false, message: `Ошибка сети: ${e.message}` };
    }
}

async function fetchPublicationPackage(productId) {
    const token = await getStoredToken();
    if (!token) {
        return { success: false, message: "Расширение не привязано к Техноребут." };
    }
    try {
        const res = await fetch(`${BRIDGE_BASE_URL}/publication-package/${productId}`, {
            method: "GET",
            headers: {
                "X-Extension-Token": token,
                "Accept": "application/json"
            }
        });
        const parsed = await parseJsonResponseSafely(res);
        if (parsed.ok) {
            return { success: true, package: parsed.data };
        }
        return { success: false, message: parsed.error, details: parsed.data };
    } catch (e) {
        return { success: false, message: `Ошибка связи с сервером: ${e.message}` };
    }
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "get_status") {
        checkBridgeStatus().then(sendResponse);
        return true;
    }
    if (request.action === "pair") {
        pairExtension(request.code).then(sendResponse);
        return true;
    }
    if (request.action === "ingest_listing") {
        sendListingPayload(request.payload).then(sendResponse);
        return true;
    }
    if (request.action === "ingest_my_listings") {
        sendMyListingsPayload(request.payload).then(sendResponse);
        return true;
    }
    if (request.action === "fetch_publication_package") {
        fetchPublicationPackage(request.product_id).then(sendResponse);
        return true;
    }
    return true;
});

