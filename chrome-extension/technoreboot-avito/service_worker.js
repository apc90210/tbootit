// Technoreboot Avito Extension Service Worker (Manifest V3 v0.2.60)

const DEFAULT_BRIDGE_BASE_URL = "http://localhost:8011/admin-api/avito-extension";

// Deprecated in Stage 09A-R4: All seller-initiated deactivations execute directly in real mode.
async function getDryRunMode() {
    return false;
}

async function setDryRunMode(enabled) {
    return Promise.resolve();
}

async function getArmedListingId() {
    return null;
}

async function setArmedListingId(listingId) {
    return Promise.resolve();
}

async function getActiveDeactivationTask() {
    return new Promise(resolve => {
        chrome.storage.local.get(["active_deactivation_task"], result => {
            resolve(result.active_deactivation_task || null);
        });
    });
}

async function setActiveDeactivationTask(task) {
    return new Promise(resolve => {
        if (!task) {
            chrome.storage.local.remove(["active_deactivation_task"], () => resolve());
        } else {
            chrome.storage.local.set({ active_deactivation_task: task }, () => resolve());
        }
    });
}

function isValidAvitoTarget(listingUrl, avitoListingId) {
    if (!listingUrl || !avitoListingId) return false;
    try {
        const parsed = new URL(listingUrl);
        if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return false;
        const host = (parsed.hostname || "").toLowerCase();
        if (host !== "avito.ru" && !host.endsWith(".avito.ru")) return false;
        if (!listingUrl.includes(String(avitoListingId))) return false;
        return true;
    } catch (e) {
        return false;
    }
}

async function getServerUrl() {
    return new Promise(resolve => {
        chrome.storage.local.get(["server_base_url"], result => {
            resolve(result.server_base_url || DEFAULT_BRIDGE_BASE_URL);
        });
    });
}

async function setServerUrl(url) {
    return new Promise(resolve => {
        chrome.storage.local.set({ server_base_url: url }, () => {
            resolve();
        });
    });
}

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
        if (res.status === 422) {
            let isMissingBody = false;
            let pydanticDetail = "";
            if (data && Array.isArray(data.detail)) {
                isMissingBody = data.detail.some(e => Array.isArray(e.loc) && e.loc.includes("body"));
                pydanticDetail = data.detail.map(e => `${(e.loc || []).join('.')}: ${e.msg || 'Поле обязательно'}`).join("; ");
            } else if (data && typeof data.detail === "string") {
                isMissingBody = data.detail.toLowerCase().includes("body");
                pydanticDetail = data.detail;
            } else if (text && text.toLowerCase().includes("body")) {
                isMissingBody = true;
            }

            const cleanError = isMissingBody
                ? "Ошибка отправки данных в Техноребут: сервер не получил пакет объявлений."
                : "Ошибка валидации данных при передаче в Техноребут.";

            return {
                ok: false,
                status: 422,
                error: cleanError,
                technical_details: pydanticDetail || "HTTP 422 Unprocessable Entity",
                data: data
            };
        }

        if (data) {
            let errMsg = null;
            if (typeof data.detail === "string") {
                errMsg = data.detail;
            } else if (data.detail && typeof data.detail === "object") {
                errMsg = data.detail.message || data.detail.error || "Ошибка обработки данных на сервере";
            } else if (data.message) {
                errMsg = data.message;
            } else if (data.error) {
                errMsg = data.error;
            }
            if (errMsg) {
                // Strip pydantic.dev links from user-facing error message
                const cleanMsg = String(errMsg).replace(/https?:\/\/errors\.pydantic\.dev[^\s"']+/gi, '').trim();
                return { ok: false, status: res.status, error: `Ошибка сервера ${res.status}: ${cleanMsg}`, data: data };
            }
        }
        const safeText = text ? text.slice(0, 150).trim().replace(/https?:\/\/errors\.pydantic\.dev[^\s"']+/gi, '') : "Internal Server Error";
        return { ok: false, status: res.status, error: `Ошибка сервера ${res.status}: ${safeText}` };
    }
}

async function checkBridgeStatus() {
    try {
        const bridgeUrl = await getServerUrl();
        const token = await getStoredToken();
        const res = await fetch(`${bridgeUrl}/status`, {
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
                version: data.version || "0.1.9",
                server_url: bridgeUrl
            };
        }
        return { online: false, error: parsed.error, server_url: bridgeUrl };
    } catch (e) {
        const bridgeUrl = await getServerUrl();
        return { online: false, error: e.message, server_url: bridgeUrl };
    }
}

async function pairExtension(code, serverUrl) {
    try {
        // If a server URL is provided, store it and use it for pairing
        if (serverUrl) {
            await setServerUrl(serverUrl);
        }
        const bridgeUrl = await getServerUrl();
        const res = await fetch(`${bridgeUrl}/pairing/pair`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pair_code: code })
        });
        const parsed = await parseJsonResponseSafely(res);
        if (parsed.ok && parsed.data.status === "paired" && parsed.data.extension_token) {
            await setStoredToken(parsed.data.extension_token);
            return { success: true, message: "Расширение успешно привязано к Техноребут!", server_url: bridgeUrl };
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
        const bridgeUrl = await getServerUrl();
        const res = await fetch(`${bridgeUrl}/listing`, {
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

async function sendBulkImportPayload(payload) {
    const token = await getStoredToken();
    if (!token) {
        return { success: false, message: "Расширение не привязано к Техноребут." };
    }
    try {
        let normalizedPayload = payload;
        if (!normalizedPayload) {
            normalizedPayload = { items: [] };
        } else if (Array.isArray(normalizedPayload)) {
            normalizedPayload = { items: normalizedPayload };
        } else if (typeof normalizedPayload === "object") {
            if (!Array.isArray(normalizedPayload.items)) {
                normalizedPayload.items = normalizedPayload.items ? [normalizedPayload.items] : [];
            }
        } else {
            normalizedPayload = { items: [] };
        }

        if (!normalizedPayload.schema_version) {
            normalizedPayload.schema_version = 1;
        }
        normalizedPayload.extension_version = "0.2.60";
        if (!normalizedPayload.captured_at) {
            normalizedPayload.captured_at = new Date().toISOString();
        }
        if (!normalizedPayload.page_type) {
            normalizedPayload.page_type = "bulk_import";
        }
        normalizedPayload.listings_count = normalizedPayload.items.length;

        const bodyJson = JSON.stringify(normalizedPayload);

        const bridgeUrl = await getServerUrl();
        const res = await fetch(`${bridgeUrl}/bulk-import`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Extension-Token": token
            },
            body: bodyJson
        });
        const parsed = await parseJsonResponseSafely(res);
        if (parsed.ok) {
            const data = parsed.data;
            const errList = Array.isArray(data.errors) ? data.errors : [];
            const errCount = data.error_count != null ? data.error_count : errList.length;
            const createdCount = data.created || 0;
            const updatedCount = data.updated || 0;
            const skippedCount = data.skipped || 0;
            const totalCount = data.total != null ? data.total : (data.count != null ? data.count : normalizedPayload.items.length);

            return {
                success: true,
                total: totalCount,
                count: totalCount,
                created: createdCount,
                updated: updatedCount,
                skipped: skippedCount,
                errors: errList,
                error_count: errCount,
                results: data.results || [],
                message: `Обработано: ${totalCount}. Создано: ${createdCount}, Обновлено: ${updatedCount}, Ошибок: ${errCount}.`,
                details: data
            };
        }
        return {
            success: false,
            message: parsed.error || "Ошибка массового импорта",
            technical_details: parsed.technical_details,
            details: parsed.data,
            error_count: normalizedPayload.items.length,
            errors: normalizedPayload.items.map(it => ({
                avito_id: it.avito_id,
                error: parsed.error || "Ошибка массового импорта"
            }))
        };
    } catch (e) {
        return { success: false, message: `Ошибка сети: ${e.message}` };
    }
}

async function sendMyListingsPayload(payload) {
    return sendBulkImportPayload(payload);
}

async function fetchPublicationPackage(productId) {
    const token = await getStoredToken();
    if (!token) {
        return { success: false, message: "Расширение не привязано к Техноребут." };
    }
    try {
        const bridgeUrl = await getServerUrl();
        const res = await fetch(`${bridgeUrl}/publication-package/${productId}`, {
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

async function downloadPhotoFromCdn(candidateUrls, maxBytes = 20 * 1024 * 1024) {
    const urls = Array.isArray(candidateUrls) ? candidateUrls : (candidateUrls ? [candidateUrls] : []);
    if (urls.length === 0) {
        return { success: false, error: "No candidate URLs provided", candidate_count: 0 };
    }
    let lastError = null;

    for (let i = 0; i < urls.length; i++) {
        const url = urls[i];
        if (!url || typeof url !== "string") continue;
        try {
            let parsedUrl;
            try {
                parsedUrl = new URL(url);
            } catch (e) {
                lastError = `Invalid URL: ${url}`;
                continue;
            }
            const host = parsedUrl.hostname.toLowerCase();
            if (!host.endsWith(".img.avito.st") && host !== "img.avito.st") {
                lastError = `Forbidden CDN host: ${host}`;
                continue;
            }

            const res = await fetch(url, {
                method: "GET",
                credentials: "omit"
            });
            if (!res.ok) {
                lastError = `HTTP ${res.status} from ${url}`;
                continue;
            }

            const contentType = res.headers.get("content-type") || "";
            if (!contentType.toLowerCase().startsWith("image/")) {
                lastError = `Non-image Content-Type '${contentType}' from ${url}`;
                continue;
            }

            const arrayBuffer = await res.arrayBuffer();
            if (arrayBuffer.byteLength > maxBytes) {
                lastError = `Image exceeds max byte limit (${arrayBuffer.byteLength} > ${maxBytes})`;
                continue;
            }
            if (arrayBuffer.byteLength === 0) {
                lastError = `Empty image response from ${url}`;
                continue;
            }

            let binary = "";
            const bytes = new Uint8Array(arrayBuffer);
            const len = bytes.byteLength;
            const chunkSize = 8192;
            for (let j = 0; j < len; j += chunkSize) {
                binary += String.fromCharCode.apply(null, bytes.subarray(j, Math.min(j + chunkSize, len)));
            }
            const base64Str = btoa(binary);

            let sha256Hex = null;
            try {
                const hashBuffer = await crypto.subtle.digest("SHA-256", arrayBuffer);
                const hashArray = Array.from(new Uint8Array(hashBuffer));
                sha256Hex = hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
            } catch (e) {}

            return {
                success: true,
                selected_url: url,
                candidate_index: i,
                candidate_count: urls.length,
                content_type: contentType,
                bytes: len,
                sha256: sha256Hex,
                base64: base64Str
            };
        } catch (err) {
            lastError = err.message || `Fetch error for ${url}`;
        }
    }

    return {
        success: false,
        error: lastError || "All photo candidates failed to download",
        candidate_count: urls.length
    };
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "get_status") {
        checkBridgeStatus().then(sendResponse);
        return true;
    }
    if (request.action === "pair") {
        pairExtension(request.code, request.server_url).then(sendResponse);
        return true;
    }
    if (request.action === "set_server_url") {
        setServerUrl(request.server_url).then(() => {
            sendResponse({ success: true });
        });
        return true;
    }
    if (request.action === "ingest_listing") {
        sendListingPayload(request.payload).then(sendResponse);
        return true;
    }
    if (request.action === "ingest_my_listings" || request.action === "bulk_import_batch") {
        const payload = request.payload || (request.items ? { items: request.items } : null);
        sendBulkImportPayload(payload).then(sendResponse);
        return true;
    }
    if (request.action === "fetch_publication_package") {
        fetchPublicationPackage(request.product_id).then(sendResponse);
        return true;
    }
    if (request.action === "download_photo_candidate") {
        downloadPhotoFromCdn(request.candidate_urls, request.max_bytes).then(sendResponse);
        return true;
    }
    if (request.action === "fetch_next_task") {
        fetchNextPostSaleTask().then(sendResponse);
        return true;
    }
    if (request.action === "report_task_success") {
        reportTaskSuccess(request.task_id, request.result_data).then(sendResponse);
        return true;
    }
    if (request.action === "report_task_failed") {
        reportTaskFailed(request.task_id, request.error, request.can_retry).then(sendResponse);
        return true;
    }
    if (request.action === "get_active_task") {
        getActiveDeactivationTask().then(task => sendResponse({ task: task }));
        return true;
    }
    if (request.action === "get_dry_run_mode") {
        getDryRunMode().then(isDryRun => sendResponse({ dry_run: isDryRun }));
        return true;
    }
    if (request.action === "set_dry_run_mode") {
        setDryRunMode(request.enabled).then(() => sendResponse({ success: true, dry_run: request.enabled }));
        return true;
    }
    if (request.action === "get_armed_listing_id") {
        getArmedListingId().then(id => sendResponse({ armed_listing_id: id }));
        return true;
    }
    if (request.action === "arm_specific_listing") {
        const id = request.listing_id ? String(request.listing_id).trim() : null;
        setArmedListingId(id).then(() => {
            const isDry = !id;
            setDryRunMode(isDry).then(() => {
                sendResponse({ success: true, armed_listing_id: id, dry_run: isDry });
            });
        });
        return true;
    }
    if (request.action === "clear_active_task") {
        setActiveDeactivationTask(null).then(() => sendResponse({ success: true }));
        return true;
    }
    if (request.action === "trigger_poll_tasks") {
        pollNextDeactivationTask().then(() => sendResponse({ success: true }));
        return true;
    }
    return true;
});

async function fetchNextPostSaleTask() {
    const token = await getStoredToken();
    if (!token) {
        return { success: false, message: "Расширение не привязано к Техноребут." };
    }
    try {
        const bridgeUrl = await getServerUrl();
        const res = await fetch(`${bridgeUrl}/tasks/next`, {
            method: "GET",
            headers: {
                "X-Extension-Token": token,
                "Accept": "application/json"
            }
        });
        const parsed = await parseJsonResponseSafely(res);
        if (parsed.ok) {
            return { success: true, task: parsed.data.task || null };
        }
        return { success: false, message: parsed.error, details: parsed.data };
    } catch (e) {
        return { success: false, message: `Ошибка связи: ${e.message}` };
    }
}

async function notifyTaskStarted(taskId) {
    const token = await getStoredToken();
    if (!token) return { success: false, message: "Не привязано" };
    try {
        const bridgeUrl = await getServerUrl();
        const res = await fetch(`${bridgeUrl}/tasks/${taskId}/started`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Extension-Token": token
            }
        });
        const parsed = await parseJsonResponseSafely(res);
        return { success: parsed.ok, data: parsed.data };
    } catch (e) {
        return { success: false, message: e.message };
    }
}

async function reportTaskSuccess(taskId, resultData = {}) {
    const token = await getStoredToken();
    if (!token) return { success: false, message: "Не привязано" };
    try {
        const bridgeUrl = await getServerUrl();
        const res = await fetch(`${bridgeUrl}/tasks/${taskId}/success`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Extension-Token": token
            },
            body: JSON.stringify(resultData)
        });
        const parsed = await parseJsonResponseSafely(res);
        return { success: parsed.ok, data: parsed.data };
    } catch (e) {
        return { success: false, message: e.message };
    }
}

async function reportTaskFailed(taskId, errorMsg, canRetry = true) {
    const token = await getStoredToken();
    if (!token) return { success: false, message: "Не привязано" };
    try {
        const bridgeUrl = await getServerUrl();
        const res = await fetch(`${bridgeUrl}/tasks/${taskId}/failed`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Extension-Token": token
            },
            body: JSON.stringify({ error: errorMsg, can_retry: canRetry })
        });
        const parsed = await parseJsonResponseSafely(res);
        return { success: parsed.ok, data: parsed.data };
    } catch (e) {
        return { success: false, message: e.message };
    }
}

let isPollingActive = false;

async function pollNextDeactivationTask() {
    if (isPollingActive) return;
    isPollingActive = true;
    try {
        const token = await getStoredToken();
        if (!token) return; // Only poll when paired

        // Active task lock check: ONE TASK AT A TIME
        const activeTask = await getActiveDeactivationTask();
        if (activeTask && activeTask.task_id) {
            const updatedAt = activeTask.updated_at ? new Date(activeTask.updated_at).getTime() : 0;
            const now = Date.now();
            // Lock timeout after 5 minutes to recover safely from suspended/crashed worker
            if (updatedAt && (now - updatedAt > 300000)) {
                console.warn("[AvitoSW] Active task timed out after 5 minutes, clearing lock:", activeTask.task_id);
                await reportTaskFailed(activeTask.task_id, "Extension task execution timed out (5 min)", false);
                await setActiveDeactivationTask(null);
            } else {
                // Task is actively locked in progress
                return;
            }
        }

        const res = await fetchNextPostSaleTask();
        if (!res || !res.success || !res.task) return;
        const task = res.task;

        // Strict target validation
        const SUPPORTED_DEACTIVATION_ACTIONS = ["deactivate_listing", "deactivate"];
        if (!SUPPORTED_DEACTIVATION_ACTIONS.includes(task.action)) {
            console.warn("[AvitoSW] Unsupported task action:", task.action);
            await reportTaskFailed(task.task_id, `Unsupported action: ${task.action}`, false);
            return;
        }

        if (!isValidAvitoTarget(task.listing_url, task.avito_listing_id)) {
            console.error("[AvitoSW] Target validation failed for task:", task);
            await reportTaskFailed(task.task_id, `Security validation failed: invalid target URL or ID (${task.listing_url})`, false);
            return;
        }

        // Notify server that task is started/processing
        await notifyTaskStarted(task.task_id);

        // Stage 09A-R4: All seller-initiated deactivations execute directly in real mode
        const initialTaskState = {
            task_id: task.task_id,
            sale_id: task.sale_id,
            product_id: task.product_id,
            action: task.action,
            avito_listing_id: String(task.avito_listing_id),
            listing_url: task.listing_url,
            step: "received",
            status_message: `Задача #${task.task_id}: снятие с публикации №${task.avito_listing_id}`,
            tab_id: null,
            dry_run: false,
            updated_at: new Date().toISOString()
        };
        await setActiveDeactivationTask(initialTaskState);

        // Execute direct real deactivation navigation and DOM interaction
        await executeDeactivationFlow(initialTaskState);
    } catch (e) {
        console.error("[AvitoSW] pollNextDeactivationTask error:", e);
    } finally {
        isPollingActive = false;
    }
}

async function executeDeactivationFlow(task) {
    try {
        task.step = "opening_page";
        task.status_message = `Открываю объявление Avito №${task.avito_listing_id}...`;
        task.updated_at = new Date().toISOString();
        await setActiveDeactivationTask(task);

        // Track previously active tab to restore focus later
        let originalTabId = null;
        try {
            const [currentActiveTab] = await new Promise(r => chrome.tabs.query({ active: true, currentWindow: true }, r));
            originalTabId = currentActiveTab ? currentActiveTab.id : null;
        } catch (_) {}

        // Find existing tab with this Avito ID or open a new tab
        const allTabs = await new Promise(r => chrome.tabs.query({}, r));
        let targetTab = allTabs.find(t => t.url && t.url.includes(task.avito_listing_id));

        if (targetTab) {
            await new Promise(r => chrome.tabs.update(targetTab.id, { active: true }, r));
            task.tab_id = targetTab.id;
        } else {
            targetTab = await new Promise(r => chrome.tabs.create({ url: task.listing_url, active: true }, r));
            task.tab_id = targetTab.id;
        }

        // Wait for page to fully load
        const loaded = await waitForTabComplete(targetTab.id, 25000);
        if (!loaded) {
            task.step = "failed";
            task.status_message = "Страница объявления Avito не загрузилась вовремя.";
            task.updated_at = new Date().toISOString();
            await setActiveDeactivationTask(task);
            await reportTaskFailed(task.task_id, task.status_message, true);
            setTimeout(async () => {
                await setActiveDeactivationTask(null);
            }, 3000);
            return;
        }

        task.step = "verifying_id";
        task.status_message = `Проверяю ID объявления №${task.avito_listing_id} на странице...`;
        task.updated_at = new Date().toISOString();
        await setActiveDeactivationTask(task);

        // Send execution command to content script
        const response = await sendTabMessageWithRetry(targetTab.id, {
            action: "execute_deactivation",
            task: task
        }, 5);

        if (!response) {
            task.step = "failed";
            task.status_message = "Content script не ответил на команду деактивации.";
            task.updated_at = new Date().toISOString();
            await setActiveDeactivationTask(task);
            await reportTaskFailed(task.task_id, task.status_message, true);
            setTimeout(async () => {
                await setActiveDeactivationTask(null);
            }, 3000);
            return;
        }

        if (response.success) {
            task.step = "confirmed";
            task.status_message = `Подтверждение получено: объявление №${task.avito_listing_id} успешно деактивировано!`;
            task.updated_at = new Date().toISOString();
            await setActiveDeactivationTask(task);
            await reportTaskSuccess(task.task_id, response.details || {});
            console.log("[AvitoSW] Real deactivation confirmed and reported to server.");

            // Restore focus to original tab and safely close temporary task tab after brief delay
            if (originalTabId && targetTab && originalTabId !== targetTab.id) {
                try {
                    await new Promise(r => chrome.tabs.update(originalTabId, { active: true }, r));
                } catch (_) {}
            }
            if (targetTab && targetTab.id) {
                setTimeout(() => {
                    chrome.tabs.remove(targetTab.id).catch(() => {});
                }, 2000);
            }

            // Clear lock after 3 seconds so next task can run
            setTimeout(async () => {
                await setActiveDeactivationTask(null);
            }, 3000);
            return;
        }

        if (response.status === "manual_required") {
            task.step = "manual_required";
            task.status_message = `Требуется ручное действие: ${response.error || 'Не удалось определить кнопку снятия'}`;
            task.updated_at = new Date().toISOString();
            await setActiveDeactivationTask(task);
            await reportTaskFailed(task.task_id, task.status_message, false);
            setTimeout(async () => {
                await setActiveDeactivationTask(null);
            }, 3000);
            return;
        }

        // Generic failure
        task.step = "failed";
        task.status_message = response.error || "Ошибка выполнения деактивации.";
        task.updated_at = new Date().toISOString();
        await setActiveDeactivationTask(task);
        await reportTaskFailed(task.task_id, task.status_message, true);
        setTimeout(async () => {
            await setActiveDeactivationTask(null);
        }, 3000);
    } catch (err) {
        console.error("[AvitoSW] Execution flow error:", err);
        task.step = "failed";
        task.status_message = `Ошибка выполнения: ${err.message}`;
        task.updated_at = new Date().toISOString();
        await setActiveDeactivationTask(task);
        await reportTaskFailed(task.task_id, err.message, true);
        setTimeout(async () => {
            await setActiveDeactivationTask(null);
        }, 3000);
    }
}

function waitForTabComplete(tabId, timeoutMs = 25000) {
    return new Promise(resolve => {
        let timer = null;
        function checkTab() {
            chrome.tabs.get(tabId, tab => {
                if (chrome.runtime.lastError || !tab) {
                    clearTimeout(timer);
                    resolve(false);
                } else if (tab.status === "complete") {
                    clearTimeout(timer);
                    setTimeout(() => resolve(true), 1200);
                }
            });
        }
        function listener(updatedTabId, changeInfo) {
            if (updatedTabId === tabId && changeInfo.status === "complete") {
                chrome.tabs.onUpdated.removeListener(listener);
                clearTimeout(timer);
                setTimeout(() => resolve(true), 1200);
            }
        }
        chrome.tabs.onUpdated.addListener(listener);
        timer = setTimeout(() => {
            chrome.tabs.onUpdated.removeListener(listener);
            resolve(false);
        }, timeoutMs);
        checkTab();
    });
}

async function sendTabMessageWithRetry(tabId, message, maxRetries = 5) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            const resp = await new Promise((resolve, reject) => {
                chrome.tabs.sendMessage(tabId, message, res => {
                    if (chrome.runtime.lastError) {
                        reject(new Error(chrome.runtime.lastError.message));
                    } else {
                        resolve(res);
                    }
                });
            });
            return resp;
        } catch (e) {
            if (attempt === maxRetries) {
                // Try executing content script directly if not injected
                try {
                    await chrome.scripting.executeScript({
                        target: { tabId: tabId },
                        files: ["content.js"]
                    });
                    await new Promise(r => setTimeout(r, 600));
                    return await new Promise((resolve, reject) => {
                        chrome.tabs.sendMessage(tabId, message, res => {
                            if (chrome.runtime.lastError) reject(new Error(chrome.runtime.lastError.message));
                            else resolve(res);
                        });
                    });
                } catch (injErr) {
                    console.warn("[AvitoSW] Script injection fallback failed:", injErr);
                }
            }
            await new Promise(r => setTimeout(r, 1000));
        }
    }
    return null;
}

// Alarms and timer setup
try {
    if (typeof chrome !== "undefined" && chrome.alarms) {
        chrome.alarms.onAlarm.addListener(alarm => {
            if (alarm.name === "avito_poll_tasks") {
                pollNextDeactivationTask();
            }
        });

        chrome.runtime.onInstalled.addListener(() => {
            chrome.alarms.create("avito_poll_tasks", { periodInMinutes: 0.2 });
            pollNextDeactivationTask();
        });

        chrome.runtime.onStartup.addListener(() => {
            chrome.alarms.create("avito_poll_tasks", { periodInMinutes: 0.2 });
            pollNextDeactivationTask();
        });
    }
} catch (e) {
    console.warn("[AvitoSW] Alarms setup warning:", e);
}

// Active interval polling while service worker is running
try {
    setInterval(pollNextDeactivationTask, 10000);
} catch (e) {}



