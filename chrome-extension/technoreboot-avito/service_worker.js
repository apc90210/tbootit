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
            return { online: true, paired: data.paired === true, version: data.version };
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
        if (res.ok && data.status === "imported") {
            return {
                success: true,
                message: `Объявление ${data.external_item_id} успешно передано! (Product ID: ${data.product_id}, Результат: ${data.result})`,
                details: data
            };
        }
        return { success: false, message: data.detail || "Не удалось передать объявление." };
    } catch (e) {
        return { success: false, message: `Ошибка при передаче: ${e.message}` };
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
