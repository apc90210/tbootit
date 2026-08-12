// Technoreboot Avito Extension Service Worker (Manifest V3)

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

async function checkBridgeStatus() {
    try {
        const token = await getStoredToken();
        const res = await fetch(`${BRIDGE_BASE_URL}/status`, {
            headers: token ? { "X-Extension-Token": token } : {}
        });
        if (res.ok) {
            const data = await res.json();
            const isPaired = data.paired === true && Boolean(token);
            if (token && !data.paired) {
                await new Promise(r => chrome.storage.local.remove(["extension_token"], r));
            }
            return {
                online: true,
                paired: isPaired,
                has_token: Boolean(token),
                token_valid: data.token_valid === true,
                version: data.version || "0.1.3"
            };
        }
        return { online: false, error: `HTTP ${res.status}` };
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
        const data = await res.json();
        if (res.ok && data.status === "paired" && data.extension_token) {
            await setStoredToken(data.extension_token);
            return { success: true, message: "Расширение успешно привязано к Техноребут!" };
        }
        return { success: false, message: data.detail || "Неверный код подключения." };
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
        const data = await res.json();
        if (res.ok && (data.status === "success" || data.status === "imported") && data.product_id != null) {
            return {
                success: true,
                product_id: data.product_id,
                result: data.result,
                message: data.message || `Объявление ${data.external_item_id} успешно импортировано!`,
                details: data
            };
        }
        const errMsg = (data && data.detail && data.detail.message) ? data.detail.message : (data.detail || data.message || "Не удалось импортировать объявление.");
        return { success: false, product_id: null, message: errMsg, details: data };
    } catch (e) {
        return { success: false, product_id: null, message: `Ошибка при передаче: ${e.message}` };
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
        const data = await res.json();
        if (res.ok) {
            return { success: true, message: `Список объявлений получен (найдено: ${data.count}).`, details: data };
        }
        return { success: false, message: data.detail || "Не удалось передать список." };
    } catch (e) {
        return { success: false, message: `Ошибка: ${e.message}` };
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
    return true;
});
