// Technoreboot Avito Popup Script (v0.2.31)

document.addEventListener("DOMContentLoaded", async () => {
    const connBadge = document.getElementById("connBadge");
    const statusMsg = document.getElementById("statusMsg");
    const pairSection = document.getElementById("pairSection");
    const pairCodeInput = document.getElementById("pairCodeInput");
    const pairBtn = document.getElementById("pairBtn");
    const pairMsg = document.getElementById("pairMsg");

    // Sections
    const prepareSection = document.getElementById("prepareSection");
    const prepareTitle = document.getElementById("prepareTitle");
    const prepareDetectInfo = document.getElementById("prepareDetectInfo");
    const prepareBtn = document.getElementById("prepareBtn");
    const draftReadyControls = document.getElementById("draftReadyControls");
    const openAvitoBtn = document.getElementById("openAvitoBtn");
    const clearDraftBtn = document.getElementById("clearDraftBtn");
    const prepareMsg = document.getElementById("prepareMsg");

    const fillSection = document.getElementById("fillSection");
    const fillTitle = document.getElementById("fillTitle");
    const fillDetectInfo = document.getElementById("fillDetectInfo");
    const fillActionsContainer = document.getElementById("fillActionsContainer");
    const fillAutoBtn = document.getElementById("fillAutoBtn");
    const fillStepBtn = document.getElementById("fillStepBtn");
    const clearDraftFromAvitoBtn = document.getElementById("clearDraftFromAvitoBtn");
    const fillReportContainer = document.getElementById("fillReportContainer");
    const fillSummary = document.getElementById("fillSummary");
    const fillDetails = document.getElementById("fillDetails");
    const toggleDetailsBtn = document.getElementById("toggleDetailsBtn");
    const fillMsg = document.getElementById("fillMsg");

    const bulkSection = document.getElementById("bulkSection");
    const bulkTitle = document.getElementById("bulkTitle");
    const bulkDetectInfo = document.getElementById("bulkDetectInfo");
    const bulkActionButtons = document.getElementById("bulkActionButtons");
    const bulkImportAllBtn = document.getElementById("bulkImportAllBtn");
    const bulkImportCurrentBtn = document.getElementById("bulkImportCurrentBtn");
    const bulkStopBtn = document.getElementById("bulkStopBtn");
    const bulkProgressBox = document.getElementById("bulkProgressBox");
    const bulkProgressHeader = document.getElementById("bulkProgressHeader");
    const bulkTotalPages = document.getElementById("bulkTotalPages");
    const bulkProcessedCount = document.getElementById("bulkProcessedCount");
    const bulkFoundCount = document.getElementById("bulkFoundCount");
    const bulkCreatedCount = document.getElementById("bulkCreatedCount");
    const bulkUpdatedCount = document.getElementById("bulkUpdatedCount");
    const bulkSkippedCount = document.getElementById("bulkSkippedCount");
    const bulkErrorsCount = document.getElementById("bulkErrorsCount");
    const bulkErrorDetails = document.getElementById("bulkErrorDetails");
    const toggleBulkErrorsBtn = document.getElementById("toggleBulkErrorsBtn");
    const bulkMsg = document.getElementById("bulkMsg");

    const actionSection = document.getElementById("actionSection");
    const pageTypeTitle = document.getElementById("pageTypeTitle");
    const pageDetectInfo = document.getElementById("pageDetectInfo");
    const sendBtn = document.getElementById("sendBtn");
    const productLinkContainer = document.getElementById("productLinkContainer");
    const openProductBtn = document.getElementById("openProductBtn");
    const resultMsg = document.getElementById("resultMsg");
    const versionLabel = document.getElementById("versionLabel");

    // Dynamic version label from manifest.json
    if (versionLabel) {
        let manifestVer = "0.2.51";
        try {
            if (typeof chrome !== "undefined" && chrome.runtime && typeof chrome.runtime.getManifest === "function") {
                const manifest = chrome.runtime.getManifest();
                if (manifest && manifest.version) {
                    manifestVer = manifest.version;
                }
            }
        } catch (e) {}
        versionLabel.textContent = `Техноребут Avito v${manifestVer}`;
    }

    let currentExtractionData = null;
    let isPaired = false;
    let isServerOnline = false;

    // --- Session Storage Draft Helpers (30 min TTL) ---
    async function getSessionDraft() {
        return new Promise(resolve => {
            if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.session) {
                chrome.storage.session.get(["avito_publication_draft"], res => {
                    const draft = res ? res.avito_publication_draft : null;
                    if (!draft) return resolve(null);
                    // Check TTL
                    const now = Date.now();
                    const expiresAt = draft.expires_at ? new Date(draft.expires_at).getTime() : 0;
                    if (expiresAt && now > expiresAt) {
                        // Expired
                        chrome.storage.session.remove(["avito_publication_draft"]);
                        return resolve(null);
                    }
                    resolve(draft);
                });
            } else if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
                // Fallback to local storage if session storage is unavailable
                chrome.storage.local.get(["avito_publication_draft"], res => {
                    const draft = res ? res.avito_publication_draft : null;
                    if (!draft) return resolve(null);
                    const now = Date.now();
                    const expiresAt = draft.expires_at ? new Date(draft.expires_at).getTime() : 0;
                    if (expiresAt && now > expiresAt) {
                        chrome.storage.local.remove(["avito_publication_draft"]);
                        return resolve(null);
                    }
                    resolve(draft);
                });
            } else {
                resolve(null);
            }
        });
    }

    async function saveSessionDraft(draftData) {
        return new Promise(resolve => {
            const storageArea = (chrome.storage && chrome.storage.session) ? chrome.storage.session : chrome.storage.local;
            storageArea.set({ avito_publication_draft: draftData }, () => resolve());
        });
    }

    async function clearSessionDraft() {
        return new Promise(resolve => {
            if (chrome.storage && chrome.storage.session) {
                chrome.storage.session.remove(["avito_publication_draft"], () => {
                    if (chrome.storage.local) chrome.storage.local.remove(["avito_publication_draft"]);
                    resolve();
                });
            } else if (chrome.storage && chrome.storage.local) {
                chrome.storage.local.remove(["avito_publication_draft"], () => resolve());
            } else {
                resolve();
            }
        });
    }

    // --- Status Check ---
    chrome.runtime.sendMessage({ action: "get_status" }, response => {
        if (!response || !response.online) {
            isServerOnline = false;
            isPaired = false;
            connBadge.className = "badge badge-offline";
            connBadge.textContent = "Offline";
            statusMsg.textContent = "Сервер Техноребут недоступен (проверьте работу контейнеров).";
            hideAllCards();
        } else if (!response.paired) {
            isServerOnline = true;
            isPaired = false;
            connBadge.className = "badge badge-offline";
            connBadge.textContent = "Не привязан";
            statusMsg.textContent = "Сервер Техноребут в сети. Введите код для привязки.";
            hideAllCards();
            pairSection.style.display = "block";
            inspectActiveTab();
        } else {
            isServerOnline = true;
            isPaired = true;
            connBadge.className = "badge badge-online";
            connBadge.textContent = "Подключен";
            statusMsg.textContent = "Расширение подключено к Техноребут.";
            hideAllCards();
            inspectActiveTab();
        }
    });

    function hideAllCards() {
        pairSection.style.display = "none";
        prepareSection.style.display = "none";
        fillSection.style.display = "none";
        bulkSection.style.display = "none";
        actionSection.style.display = "none";
        if (productLinkContainer) productLinkContainer.style.display = "none";
    }

    // --- Pairing Handler ---
    pairBtn.addEventListener("click", () => {
        const rawCode = pairCodeInput.value ? pairCodeInput.value.trim() : "";
        const cleanCode = rawCode.replace(/\D/g, "");

        if (!cleanCode || cleanCode.length !== 6) {
            pairMsg.className = "msg msg-error";
            pairMsg.textContent = "Введите 6-значный цифровой код.";
            return;
        }

        pairMsg.className = "msg";
        pairMsg.textContent = "Подключение...";
        pairBtn.disabled = true;

        chrome.runtime.sendMessage({ action: "pair", code: cleanCode }, res => {
            pairBtn.disabled = false;
            if (res && res.success) {
                isPaired = true;
                connBadge.className = "badge badge-online";
                connBadge.textContent = "Подключен";
                statusMsg.textContent = "Расширение успешно привязано к серверу.";
                pairSection.style.display = "none";
                pairMsg.textContent = "";
                inspectActiveTab();
            } else {
                pairMsg.className = "msg msg-error";
                pairMsg.textContent = (res && res.message) || "Ошибка привязки кода.";
            }
        });
    });

    function sendMessageToTabWithAutoInject(tabId, message, callback) {
        chrome.tabs.sendMessage(tabId, message, response => {
            if (chrome.runtime.lastError || !response) {
                if (typeof chrome.scripting !== "undefined" && typeof chrome.scripting.executeScript === "function") {
                    chrome.scripting.executeScript({
                        target: { tabId: tabId },
                        files: ["content.js"]
                    }, () => {
                        if (chrome.runtime.lastError) {
                            callback(null);
                        } else {
                            setTimeout(() => {
                                chrome.tabs.sendMessage(tabId, message, res => {
                                    if (chrome.runtime.lastError || !res) {
                                        callback(null);
                                    } else {
                                        callback(res);
                                    }
                                });
                            }, 120);
                        }
                    });
                } else {
                    callback(null);
                }
            } else {
                callback(response);
            }
        });
    }

    function setupBulkSection(activeTab, initialResponse) {
        bulkSection.style.display = "block";
        actionSection.style.display = "none";

        const items = initialResponse.items || [];
        const pagination = initialResponse.pagination || { current_page: 1, total_pages: 1, has_next_page: false };

        bulkTitle.textContent = "Список объявлений Avito";

        if (items.length === 0) {
            bulkDetectInfo.innerHTML = `Найдено объявлений на странице: <strong>0</strong><br><span style="color: #d32f2f;">Объявления не найдены. Проверьте, что список объявлений загрузился полностью.</span> <a href="#" id="bulkRescanBtn" style="font-size: 11px; text-decoration: underline; color: #1976d2; margin-left: 4px;">Повторить поиск</a>`;
        } else {
            bulkDetectInfo.innerHTML = `Найдено объявлений на странице: <strong>${items.length}</strong><br>Страница: <strong>${pagination.current_page || 1}</strong> из <strong>${pagination.total_pages || 1}</strong>`;
        }

        const rescanBtn = document.getElementById("bulkRescanBtn");
        if (rescanBtn) {
            rescanBtn.onclick = (e) => {
                e.preventDefault();
                bulkDetectInfo.innerHTML = `Поиск объявлений на странице (ожидание загрузки)...`;
                inspectActiveTab();
            };
        }

        bulkTotalPages.textContent = pagination.total_pages || 1;
        bulkFoundCount.textContent = items.length;
        bulkProcessedCount.textContent = "0";
        bulkCreatedCount.textContent = "0";
        bulkUpdatedCount.textContent = "0";
        bulkSkippedCount.textContent = "0";
        bulkErrorsCount.textContent = "0";
        bulkErrorDetails.style.display = "none";
        toggleBulkErrorsBtn.style.display = "none";
        bulkProgressBox.style.display = "none";
        bulkStopBtn.style.display = "none";
        bulkActionButtons.style.display = "block";

        if (!isPaired) {
            bulkImportAllBtn.disabled = true;
            bulkImportCurrentBtn.disabled = true;
            bulkMsg.className = "msg msg-error";
            bulkMsg.textContent = "Импорт станет доступен после привязки расширения к серверу.";
            return;
        }

        if (items.length === 0) {
            bulkImportAllBtn.disabled = true;
            bulkImportCurrentBtn.disabled = true;
            bulkMsg.className = "msg msg-warning";
            bulkMsg.textContent = "Объявления не найдены. Проверьте, что список объявлений загрузился полностью.";
        } else {
            bulkImportAllBtn.disabled = false;
            bulkImportCurrentBtn.disabled = false;
            bulkMsg.textContent = "";
        }

        let cancelRequested = false;

        function sanitizeErrorMessage(err) {
            if (!err) return "Неизвестная ошибка";
            if (typeof err === "object") {
                if (err.error) return sanitizeErrorMessage(err.error);
                if (err.message) return sanitizeErrorMessage(err.message);
                return JSON.stringify(err);
            }
            let s = String(err);
            if (s.includes("Field required") && s.includes("body")) {
                return "Ошибка отправки данных в Техноребут: сервер не получил пакет объявлений.";
            }
            s = s.replace(/https?:\/\/errors\.pydantic\.dev[^\s"']+/gi, '').trim();
            return s;
        }

        async function saveBulkSessionState(state) {
            try {
                const storageArea = (chrome.storage && chrome.storage.session) ? chrome.storage.session : chrome.storage.local;
                if (storageArea) {
                    await new Promise(r => storageArea.set({ bulk_import_session: state }, r));
                }
            } catch (e) {}
        }

        async function getBulkSessionState() {
            try {
                const storageArea = (chrome.storage && chrome.storage.session) ? chrome.storage.session : chrome.storage.local;
                if (storageArea) {
                    return new Promise(resolve => {
                        storageArea.get(["bulk_import_session"], res => resolve(res ? res.bulk_import_session : null));
                    });
                }
            } catch (e) {}
            return null;
        }

        // Canonical batch submission helper for both current-page and multi-page flows
        async function sendBulkBatch(batchItems) {
            if (!Array.isArray(batchItems)) {
                batchItems = batchItems ? [batchItems] : [];
            }
            const payload = {
                schema_version: 1,
                extension_version: "0.2.51",
                captured_at: new Date().toISOString(),
                page_type: "bulk_import",
                listings_count: batchItems.length,
                items: batchItems
            };

            return new Promise(resolve => {
                chrome.runtime.sendMessage({
                    action: "bulk_import_batch",
                    payload: payload,
                    items: batchItems
                }, res => {
                    if (!res) {
                        resolve({
                            success: false,
                            message: "Нет ответа от background worker",
                            error_count: batchItems.length,
                            errors: batchItems.map(it => ({
                                avito_id: it.avito_id,
                                error: "Нет ответа от background worker"
                            }))
                        });
                    } else {
                        resolve(res);
                    }
                });
            });
        }

        function waitForTabLoad(tabId, timeoutMs = 15000) {
            return new Promise(resolve => {
                let resolved = false;
                const timer = setTimeout(() => {
                    if (!resolved) {
                        resolved = true;
                        chrome.tabs.onUpdated.removeListener(onUpdatedListener);
                        resolve(false);
                    }
                }, timeoutMs);

                function onUpdatedListener(updatedTabId, changeInfo) {
                    if (updatedTabId === tabId && changeInfo.status === 'complete') {
                        if (!resolved) {
                            resolved = true;
                            clearTimeout(timer);
                            chrome.tabs.onUpdated.removeListener(onUpdatedListener);
                            resolve(true);
                        }
                    }
                }
                chrome.tabs.onUpdated.addListener(onUpdatedListener);
            });
        }

        // 1. Current Page Import
        bulkImportCurrentBtn.onclick = async () => {
            if (!isPaired) return;
            bulkImportAllBtn.disabled = true;
            bulkImportCurrentBtn.disabled = true;
            bulkProgressBox.style.display = "block";
            bulkProgressHeader.textContent = "Импорт текущей страницы...";
            bulkMsg.className = "msg";
            bulkMsg.textContent = "Сбор данных и отправка в Техноребут...";

            sendMessageToTabWithAutoInject(activeTab.id, { action: "extract_current_page", maxWaitMs: 10000 }, async freshResp => {
                const curItems = (freshResp && freshResp.items) || items || [];
                if (!curItems.length) {
                    bulkImportAllBtn.disabled = false;
                    bulkImportCurrentBtn.disabled = false;
                    bulkMsg.className = "msg msg-warning";
                    bulkMsg.textContent = "Объявления не найдены на текущей странице. Проверьте, что список объявлений загрузился полностью.";
                    return;
                }

                bulkFoundCount.textContent = curItems.length;
                const res = await sendBulkBatch(curItems);
                bulkImportAllBtn.disabled = false;
                bulkImportCurrentBtn.disabled = false;

                if (res && res.success) {
                    const created = res.created || 0;
                    const updated = res.updated || 0;
                    const skipped = res.skipped || 0;
                    const errList = Array.isArray(res.errors) ? res.errors : [];
                    const errCount = res.error_count != null ? res.error_count : errList.length;

                    bulkProcessedCount.textContent = (created + updated + skipped);
                    bulkCreatedCount.textContent = created;
                    bulkUpdatedCount.textContent = updated;
                    bulkSkippedCount.textContent = skipped;
                    bulkErrorsCount.textContent = errCount;

                    if (errCount === 0 && (created + updated + skipped) > 0) {
                        bulkMsg.className = "msg msg-success";
                        bulkMsg.innerHTML = `✓ Текущая страница импортирована!<br>Отправлено: <strong>${curItems.length}</strong>, создано: <strong>${created}</strong>, обновлено: <strong>${updated}</strong>, пропущено: <strong>${skipped}</strong>`;
                    } else if (errCount > 0) {
                        bulkMsg.className = "msg msg-warning";
                        bulkMsg.innerHTML = `⚠️ Текущая страница импортирована с ошибками.<br>Отправлено: <strong>${curItems.length}</strong>, создано: <strong>${created}</strong>, обновлено: <strong>${updated}</strong>, ошибок: <strong>${errCount}</strong>`;
                    } else {
                        bulkMsg.className = "msg msg-warning";
                        bulkMsg.innerHTML = `⚠️ Ни одно объявление не было сохранено.`;
                    }

                    if (errCount > 0 && errList.length > 0) {
                        toggleBulkErrorsBtn.style.display = "inline-block";
                        bulkErrorDetails.innerHTML = errList.slice(0, 10).map(e => `<div>${e.avito_id ? 'Объявление ' + e.avito_id + ': ' : ''}${sanitizeErrorMessage(e.error || e)}</div>`).join("");
                        toggleBulkErrorsBtn.onclick = () => {
                            bulkErrorDetails.style.display = bulkErrorDetails.style.display === "none" ? "block" : "none";
                            toggleBulkErrorsBtn.textContent = bulkErrorDetails.style.display === "none" ? "Показать ошибки..." : "Скрыть ошибки";
                        };
                    }
                } else {
                    // Full batch failure
                    const errMsg = sanitizeErrorMessage((res && res.message) || "Ошибка отправки пакета");
                    bulkProcessedCount.textContent = "0";
                    bulkCreatedCount.textContent = "0";
                    bulkUpdatedCount.textContent = "0";
                    bulkSkippedCount.textContent = "0";
                    bulkErrorsCount.textContent = curItems.length;

                    bulkMsg.className = "msg msg-error";
                    bulkMsg.innerHTML = `✕ Страница не импортирована:<br>${errMsg}`;

                    toggleBulkErrorsBtn.style.display = "inline-block";
                    bulkErrorDetails.innerHTML = `<div>Ошибка пакета (HTTP 422/сеть): ${errMsg}</div>`;
                    toggleBulkErrorsBtn.onclick = () => {
                        bulkErrorDetails.style.display = bulkErrorDetails.style.display === "none" ? "block" : "none";
                        toggleBulkErrorsBtn.textContent = bulkErrorDetails.style.display === "none" ? "Показать ошибки..." : "Скрыть ошибки";
                    };
                }
            });
        };

        // 2. All Pages Import
        bulkImportAllBtn.onclick = async () => {
            if (!isPaired) return;
            cancelRequested = false;

            bulkActionButtons.style.display = "none";
            bulkStopBtn.style.display = "block";
            bulkStopBtn.disabled = false;
            bulkStopBtn.textContent = "Остановить импорт";
            bulkProgressBox.style.display = "block";
            bulkProgressHeader.textContent = "Пакетный импорт всех страниц...";
            bulkMsg.className = "msg";
            bulkMsg.textContent = "Запуск импорта...";

            bulkStopBtn.onclick = () => {
                cancelRequested = true;
                bulkStopBtn.disabled = true;
                bulkStopBtn.textContent = "Остановка...";
                bulkMsg.className = "msg msg-warning";
                bulkMsg.textContent = "Завершение текущей страницы и остановка...";
            };

            let totalCreated = 0;
            let totalUpdated = 0;
            let totalSkipped = 0;
            let allErrors = [];
            const seenAvitoIds = new Set();
            const visitedUrls = new Set();
            const MAX_PAGES = 50;
            let pagesCount = 0;
            let totalPagesReported = pagination.total_pages || 1;
            let fatalBatchError = false;
            let fatalBatchMessage = "";

            try {
                while (pagesCount < MAX_PAGES && !cancelRequested) {
                    pagesCount++;
                    bulkProgressHeader.textContent = `Обработка страницы ${pagesCount}...`;

                    // Multi-attempt extraction to tolerate dynamic React rendering on navigated page
                    let pageData = null;
                    for (let attempt = 0; attempt < 3; attempt++) {
                        pageData = await new Promise(res => {
                            sendMessageToTabWithAutoInject(activeTab.id, { action: "extract_current_page", maxWaitMs: 12000 }, resp => res(resp));
                        });
                        if (pageData && pageData.items && pageData.items.length > 0) {
                            break;
                        }
                        if (attempt < 2) {
                            await new Promise(r => setTimeout(r, 1000));
                        }
                    }

                    if (!pageData || !pageData.items || pageData.items.length === 0) {
                        break;
                    }

                    const pagePagination = pageData.pagination || {};
                    if (pagePagination.total_pages && pagePagination.total_pages > totalPagesReported) {
                        totalPagesReported = pagePagination.total_pages;
                    }
                    bulkTotalPages.textContent = totalPagesReported || pagesCount;

                    const newItems = [];
                    for (const it of pageData.items) {
                        if (it.avito_id && !seenAvitoIds.has(it.avito_id)) {
                            seenAvitoIds.add(it.avito_id);
                            newItems.push(it);
                        }
                    }

                    bulkFoundCount.textContent = seenAvitoIds.size;

                    if (newItems.length > 0) {
                        const batchRes = await sendBulkBatch(newItems);
                        if (batchRes && batchRes.success) {
                            totalCreated += (batchRes.created || 0);
                            totalUpdated += (batchRes.updated || 0);
                            totalSkipped += (batchRes.skipped || 0);
                            if (batchRes.errors && batchRes.errors.length) {
                                allErrors = allErrors.concat(batchRes.errors);
                            } else if (batchRes.error_count && batchRes.error_count > 0) {
                                allErrors.push({ page: pagesCount, error: `Ошибок в пакете: ${batchRes.error_count}` });
                            }
                        } else {
                            fatalBatchError = true;
                            fatalBatchMessage = sanitizeErrorMessage((batchRes && batchRes.message) || "Ошибка отправки пакета");
                            for (const it of newItems) {
                                allErrors.push({
                                    page: pagesCount,
                                    avito_id: it.avito_id,
                                    error: fatalBatchMessage
                                });
                            }
                            break;
                        }
                    }

                    // Accounting invariant:
                    // totalCreated + totalUpdated + totalSkipped + allErrors.length == seenAvitoIds.size
                    const totalProcessedSuccess = totalCreated + totalUpdated + totalSkipped;
                    bulkProcessedCount.textContent = totalProcessedSuccess;
                    bulkCreatedCount.textContent = totalCreated;
                    bulkUpdatedCount.textContent = totalUpdated;
                    bulkSkippedCount.textContent = totalSkipped;
                    bulkErrorsCount.textContent = allErrors.length;

                    // Persist session state across tab navigation
                    await saveBulkSessionState({
                        in_progress: true,
                        currentPage: pagesCount,
                        totalPages: totalPagesReported,
                        totalUniqueSubmitted: seenAvitoIds.size,
                        totalCreated: totalCreated,
                        totalUpdated: totalUpdated,
                        totalSkipped: totalSkipped,
                        totalErrors: allErrors.length,
                        allErrors: allErrors,
                        seenAvitoIds: Array.from(seenAvitoIds),
                        visitedUrls: Array.from(visitedUrls),
                        lastUpdated: Date.now()
                    });

                    if (cancelRequested || fatalBatchError) break;

                    if (!pagePagination.has_next_page || !pagePagination.next_page_url) {
                        break;
                    }

                    const nextUrl = pagePagination.next_page_url;
                    if (visitedUrls.has(nextUrl)) {
                        break;
                    }
                    visitedUrls.add(nextUrl);

                    bulkMsg.textContent = `Переход на страницу ${pagesCount + 1}...`;
                    await new Promise(r => setTimeout(r, 1200));
                    if (cancelRequested) break;

                    chrome.tabs.update(activeTab.id, { url: nextUrl });
                    await waitForTabLoad(activeTab.id);
                    await new Promise(r => setTimeout(r, 1500));
                }
            } catch (err) {
                allErrors.push({ error: String(err) });
            } finally {
                bulkActionButtons.style.display = "block";
                bulkStopBtn.style.display = "none";
                bulkStopBtn.disabled = false;
                bulkStopBtn.textContent = "Остановить импорт";
                bulkImportAllBtn.disabled = false;
                bulkImportCurrentBtn.disabled = false;

                const totalProcessed = totalCreated + totalUpdated + totalSkipped;
                bulkProcessedCount.textContent = totalProcessed;
                bulkCreatedCount.textContent = totalCreated;
                bulkUpdatedCount.textContent = totalUpdated;
                bulkSkippedCount.textContent = totalSkipped;
                bulkErrorsCount.textContent = allErrors.length;

                // Save final session state
                await saveBulkSessionState({
                    in_progress: false,
                    completed: true,
                    currentPage: pagesCount,
                    totalPages: totalPagesReported,
                    totalUniqueSubmitted: seenAvitoIds.size,
                    totalCreated: totalCreated,
                    totalUpdated: totalUpdated,
                    totalSkipped: totalSkipped,
                    totalErrors: allErrors.length,
                    allErrors: allErrors,
                    seenAvitoIds: Array.from(seenAvitoIds),
                    visitedUrls: Array.from(visitedUrls),
                    lastUpdated: Date.now()
                });

                if (cancelRequested) {
                    bulkMsg.className = "msg msg-warning";
                    bulkMsg.innerHTML = `⚠️ Импорт остановлен пользователем.<br>Страниц обработано: <strong>${pagesCount}</strong>, создано: <strong>${totalCreated}</strong>, обновлено: <strong>${totalUpdated}</strong>, ошибок: <strong>${allErrors.length}</strong>.`;
                } else if (fatalBatchError) {
                    bulkMsg.className = "msg msg-error";
                    bulkMsg.innerHTML = `✕ Импорт остановлен из-за ошибки.<br>Страница ${pagesCount} не импортирована:<br>${fatalBatchMessage}`;
                } else if (totalProcessed === 0 || seenAvitoIds.size === 0) {
                    bulkMsg.className = "msg msg-warning";
                    bulkMsg.innerHTML = `⚠️ Объявления не найдены.<br>Проверьте, что список объявлений загрузился полностью.<br>Страниц обработано: <strong>${pagesCount}</strong>, объявлений: <strong>0</strong>.`;
                } else if (allErrors.length > 0) {
                    bulkMsg.className = "msg msg-warning";
                    bulkMsg.innerHTML = `⚠️ Импорт завершён с ошибками.<br>Страниц обработано: <strong>${pagesCount}</strong> из <strong>${totalPagesReported || pagesCount}</strong><br>Создано: <strong>${totalCreated}</strong>, обновлено: <strong>${totalUpdated}</strong>, ошибок: <strong>${allErrors.length}</strong>`;
                } else {
                    bulkMsg.className = "msg msg-success";
                    bulkMsg.innerHTML = `✓ Импорт успешно завершен!<br>Страниц обработано: <strong>${pagesCount}</strong> из <strong>${totalPagesReported || pagesCount}</strong>, объявлений: <strong>${seenAvitoIds.size}</strong><br>Создано новых: <strong>${totalCreated}</strong>, обновлено: <strong>${totalUpdated}</strong>, ошибок: <strong>0</strong>`;
                }

                if (allErrors.length > 0) {
                    toggleBulkErrorsBtn.style.display = "inline-block";
                    bulkErrorDetails.innerHTML = allErrors.slice(0, 10).map(e => `<div>${e.avito_id ? 'Объявление ' + e.avito_id + ': ' : (e.page ? 'Страница ' + e.page + ': ' : '')}${sanitizeErrorMessage(e.error || e)}</div>`).join("");
                    toggleBulkErrorsBtn.onclick = () => {
                        bulkErrorDetails.style.display = bulkErrorDetails.style.display === "none" ? "block" : "none";
                        toggleBulkErrorsBtn.textContent = bulkErrorDetails.style.display === "none" ? "Показать ошибки..." : "Скрыть ошибки";
                    };
                }
            }
        };
    }

    function setupSingleListingSection(activeTab, response) {
        actionSection.style.display = "block";
        bulkSection.style.display = "none";
        pageTypeTitle.textContent = "Карточка объявления";
        const item = response.listing || {};
        const detectedPhotosCount = (item.photos && item.photos.length) || 0;
        const visibleCount = (response.diagnostics && response.diagnostics.visible_gallery_count) || 0;
        const initialDisplayCount = Math.max(detectedPhotosCount, visibleCount);
        const displayTitle = item.title || "Объявление Avito";
        const displayPrice = item.price ? item.price + " ₽" : "Не указана";
        const photoStatusText = initialDisplayCount > 0 
            ? `Обнаружено фото: <strong>${initialDisplayCount}</strong> <span style="color:#888; font-size:11px;">(сканирование HD...)</span>`
            : `Обнаружено фото: <strong>0</strong>`;
        pageDetectInfo.innerHTML = `<strong>${displayTitle}</strong><br>ID: ${item.external_item_id || 'Авто'}<br>Цена: ${displayPrice}<br>${photoStatusText}`;
        
        if (isPaired) {
            sendBtn.disabled = false;
            sendBtn.textContent = "Доимпортировать данные";
            resultMsg.textContent = "";
        } else {
            sendBtn.disabled = true;
            sendBtn.textContent = "Доимпортировать данные";
            resultMsg.className = "msg msg-error";
            resultMsg.textContent = "Передача станет доступна после привязки расширения.";
        }

        // Run deep multi-pass scan (active gallery walker)
        chrome.tabs.sendMessage(activeTab.id, { action: "extract_current_page", deepScan: true }, deepResponse => {
            if (deepResponse && deepResponse.listing) {
                currentExtractionData = deepResponse;
                const deepCount = (deepResponse.listing.photos && deepResponse.listing.photos.length) || 0;
                const deepTitle = deepResponse.listing.title || displayTitle;
                const deepPrice = deepResponse.listing.price ? deepResponse.listing.price + " ₽" : displayPrice;
                pageDetectInfo.innerHTML = `<strong>${deepTitle}</strong><br>ID: ${deepResponse.listing.external_item_id || 'Авто'}<br>Цена: ${deepPrice}<br>Обнаружено фото: <strong>${deepCount} (все в HD)</strong> ✓`;
                if (isPaired) {
                    sendBtn.disabled = false;
                }
            }
        });
    }

    // --- Active Tab Inspector ---
    async function inspectActiveTab() {
        hideAllCards();
        if (!isPaired) {
            pairSection.style.display = "block";
        }

        chrome.tabs.query({ active: true, currentWindow: true }, async tabs => {
            if (!tabs || tabs.length === 0) return;
            const activeTab = tabs[0];
            const tabUrl = activeTab.url || "";

            // Check URL patterns
            const productMatch = tabUrl.match(/\/inventory\/products\/(\d+)/) || tabUrl.match(/\/products\/(\d+)/);
            const isAvitoHost = tabUrl.includes("avito.ru");
            const isAvitoAddItem = isAvitoHost && (tabUrl.includes("/additem") || tabUrl.includes("/add_item"));

            // 1. CONTEXT A: Technoreboot Product Card
            if (productMatch) {
                const productId = parseInt(productMatch[1], 10);
                prepareSection.style.display = "block";
                prepareTitle.textContent = `Товар #${productId}`;
                prepareDetectInfo.innerHTML = `Страница товара в Техноребут.<br>ID: <strong>${productId}</strong>`;

                const activeDraft = await getSessionDraft();
                if (activeDraft && activeDraft.product_id === productId) {
                    draftReadyControls.style.display = "block";
                    prepareBtn.textContent = "🔄 Обновить черновик";
                    prepareMsg.className = "msg msg-success";
                    prepareMsg.innerHTML = `✓ Черновик готов для публикации.<br>Заголовок: <strong>${activeDraft.title || 'Товар'}</strong>`;
                } else {
                    draftReadyControls.style.display = "none";
                    prepareBtn.textContent = "📦 Подготовить для Avito";
                    prepareMsg.textContent = "";
                }

                // Prepare Button Click
                prepareBtn.onclick = () => {
                    prepareBtn.disabled = true;
                    prepareMsg.className = "msg";
                    prepareMsg.textContent = "Получение пакета публикации...";

                    chrome.runtime.sendMessage({ action: "fetch_publication_package", product_id: productId }, async res => {
                        prepareBtn.disabled = false;
                        if (res && res.success && res.package) {
                            const pkg = res.package;
                            const preflight = pkg.preflight || {};

                            if (preflight.ready_for_browser_assisted === false) {
                                prepareMsg.className = "msg msg-error";
                                const errs = (preflight.errors || []).join("<br>");
                                prepareMsg.innerHTML = `✕ Товар не готов к публикации:<br>${errs}`;
                                return;
                            }

                            const draftObj = {
                                product_id: productId,
                                title: pkg.title,
                                prepared_at: pkg.prepared_at || new Date().toISOString(),
                                expires_at: pkg.expires_at || new Date(Date.now() + 30 * 60 * 1000).toISOString(),
                                package: pkg
                            };

                            await saveSessionDraft(draftObj);
                            draftReadyControls.style.display = "block";
                            prepareBtn.textContent = "🔄 Обновить черновик";
                            prepareMsg.className = "msg msg-success";
                            const photoCount = (pkg.photos && pkg.photos.length) || 0;
                            const charCount = Object.keys(pkg.characteristics || {}).length;
                            prepareMsg.innerHTML = `✓ Черновик подготовлен!<br>Заголовок: <strong>${pkg.title}</strong><br>Цена: <strong>${pkg.price} ₽</strong><br>Характеристик: <strong>${charCount}</strong>, фото: <strong>${photoCount}</strong>`;
                        } else {
                            prepareMsg.className = "msg msg-error";
                            prepareMsg.textContent = (res && res.message) || "Ошибка получения пакета публикации.";
                        }
                    });
                };

                // Open Avito Button Click (Explicit Action)
                openAvitoBtn.onclick = () => {
                    chrome.tabs.create({ url: "https://www.avito.ru/additem" });
                };

                // Clear Draft Button Click
                clearDraftBtn.onclick = async () => {
                    await clearSessionDraft();
                    draftReadyControls.style.display = "none";
                    prepareBtn.textContent = "📦 Подготовить для Avito";
                    prepareMsg.className = "msg";
                    prepareMsg.textContent = "Черновик очищен.";
                };
                return;
            }

            // 2. CONTEXT B: Avito Add-Item Form
            if (isAvitoAddItem) {
                fillSection.style.display = "block";
                const activeDraft = await getSessionDraft();

                if (activeDraft && activeDraft.package) {
                    const pkg = activeDraft.package;
                    const charCount = Object.keys(pkg.characteristics || {}).length;
                    const photoCount = (pkg.photos && pkg.photos.length) || 0;
                    const catName = (pkg.category && pkg.category.display_name) || (pkg.characteristics && pkg.characteristics['Категория']) || 'Авто';

                    fillTitle.textContent = "Черновик Техноребута";
                    fillDetectInfo.innerHTML = `Товар: <strong>${pkg.title || 'Без названия'}</strong><br>Категория: <strong>${catName}</strong><br>ID: <strong>${pkg.product_id}</strong> | Цена: <strong>${pkg.price} ₽</strong> | Состояние: <strong>${pkg.condition || 'Б/у'}</strong><br>Характеристик: <strong>${charCount}</strong> | Фото: <strong>${photoCount}</strong>`;
                    fillActionsContainer.style.display = "block";
                    fillMsg.textContent = "";

                    function combineReports(r1, r2) {
                        const filled = [...(r1.filled || []), ...(r2.filled || [])];
                        const skipped = [...(r1.skipped_nonempty || []), ...(r2.skipped_nonempty || [])];
                        const filledKeys = new Set(filled.map(f => f.source || f.target));
                        const unresFields = (r2.unresolved_fields || []).filter(u => !filledKeys.has(u.key || u.field));
                        const unresOptions = [...(r1.unresolved_options || []), ...(r2.unresolved_options || [])];
                        const protectedActions = [...(r1.protected_actions || []), ...(r2.protected_actions || [])];
                        return {
                            product_id: r2.product_id || r1.product_id,
                            category: (r2.category && r2.category.status !== 'manual_required') ? r2.category : (r1.category || { status: 'manual_required' }),
                            address: (r2.address && r2.address.status !== 'manual_required') ? r2.address : (r1.address || { status: 'manual_required' }),
                            filled,
                            skipped_nonempty: skipped,
                            unresolved_fields: unresFields,
                            unresolved_options: unresOptions,
                            protected_actions: protectedActions
                        };
                    }

                    function displayReport(report) {
                        fillReportContainer.style.display = "block";
                        const filledCount = (report.filled || []).length;
                        const skippedCount = (report.skipped_nonempty || []).length;
                        const unresFieldsCount = (report.unresolved_fields || []).length;
                        const unresOptionsCount = (report.unresolved_options || []).length;

                        let catStatusHtml = "";
                        if (report.category) {
                            if (report.category.status === 'selected') {
                                catStatusHtml = `• Категория: <span style="color:#2e7d32; font-weight:600;">✓ ${report.category.selected}</span><br>`;
                            } else if (report.category.status === 'ambiguous') {
                                const candList = (report.category.candidates || []).slice(0, 2).map(c => c.text).join(', ');
                                catStatusHtml = `• Категория: <span style="color:#e65100; font-weight:600;">⚠️ Несколько вариантов (${candList || 'требуется уточнение'})</span><br>`;
                            } else {
                                catStatusHtml = `• Категория: <span style="color:#555;">ℹ️ Ручной выбор на форме</span><br>`;
                            }
                        }

                        let addrStatusHtml = "";
                        if (report.address) {
                            if (report.address.status === 'filled') {
                                addrStatusHtml = `• Адрес: <span style="color:#2e7d32; font-weight:600;">✓ ${report.address.selected}</span><br>`;
                            } else if (report.address.status === 'ambiguous') {
                                addrStatusHtml = `• Адрес: <span style="color:#e65100; font-weight:600;">⚠️ Неоднозначный адрес (проверьте на карте)</span><br>`;
                            } else {
                                addrStatusHtml = `• Адрес: <span style="color:#555;">ℹ️ Адрес не указан в пакете (ручной ввод)</span><br>`;
                            }
                        }

                        fillSummary.innerHTML = `
                            <strong>Результат заполнения:</strong><br>
                            ${catStatusHtml}
                            ${addrStatusHtml}
                            • Заполнено полей: <strong>${filledCount}</strong><br>
                            • Пропущено (уже заполнено): <strong>${skippedCount}</strong><br>
                            • Ожидают ввода / не найдены: <strong>${unresFieldsCount}</strong><br>
                            • Не совпали варианты: <strong>${unresOptionsCount}</strong>
                        `;

                        let detailsHtml = "";
                        if (filledCount > 0) {
                            detailsHtml += "<strong>Заполненные:</strong><br>" + report.filled.map(f => `✓ ${f.target}: ${f.value}`).join("<br>") + "<br><br>";
                        }
                        if (skippedCount > 0) {
                            detailsHtml += "<strong>Уже были заполнены:</strong><br>" + report.skipped_nonempty.map(s => `- ${s.target}: ${s.existing_value}`).join("<br>") + "<br><br>";
                        }
                        if (unresFieldsCount > 0) {
                            detailsHtml += "<strong>Не сопоставлены:</strong><br>" + report.unresolved_fields.map(u => `? ${u.key || u.field || 'поле'}: ${u.reason || u.value || ''}`).join("<br>");
                        }

                        fillDetails.innerHTML = detailsHtml;
                        if (detailsHtml) {
                            toggleDetailsBtn.style.display = "block";
                            toggleDetailsBtn.onclick = () => {
                                if (fillDetails.style.display === "none") {
                                    fillDetails.style.display = "block";
                                    toggleDetailsBtn.textContent = "Скрыть подробности";
                                } else {
                                    fillDetails.style.display = "none";
                                    toggleDetailsBtn.textContent = "Подробнее...";
                                }
                            };
                        }
                    }

                    // 1. AUTO FILL ALL STEPS (Title -> Category -> Parameters -> Characteristics)
                    if (fillAutoBtn) {
                        fillAutoBtn.onclick = () => {
                            fillAutoBtn.disabled = true;
                            fillStepBtn.disabled = true;
                            fillMsg.className = "msg";
                            fillMsg.textContent = "⚡ Шаг 1: Заполнение названия и выбор категории...";

                            sendMessageToTabWithAutoInject(activeTab.id, { action: "fill_avito_form", package: pkg }, step1Report => {
                                if (!step1Report) {
                                    fillAutoBtn.disabled = false;
                                    fillStepBtn.disabled = false;
                                    fillMsg.className = "msg msg-error";
                                    fillMsg.textContent = "Не удалось связаться со страницей формы. Обновите страницу (F5).";
                                    return;
                                }

                                const categoryFilled = (step1Report.filled || []).some(f => f.type === 'category-tile' || f.source === 'category');

                                if (categoryFilled) {
                                    fillMsg.textContent = "⚡ Шаг 2: Категория выбрана. Ожидание формы параметров...";
                                    setTimeout(() => {
                                        fillMsg.textContent = "⚡ Шаг 2: Заполнение цены, состояния, описания и характеристик...";
                                        sendMessageToTabWithAutoInject(activeTab.id, { action: "fill_avito_form", package: pkg }, step2Report => {
                                            fillAutoBtn.disabled = false;
                                            fillStepBtn.disabled = false;
                                            const combined = combineReports(step1Report, step2Report || { filled: [], skipped_nonempty: [], unresolved_fields: [], unresolved_options: [] });
                                            displayReport(combined);
                                            fillMsg.className = "msg msg-success";
                                            fillMsg.innerHTML = "✓ Все доступные шаги выполнены: название, категория, цена, состояние и характеристики заполнены!";
                                        });
                                    }, 2200);
                                } else {
                                    fillAutoBtn.disabled = false;
                                    fillStepBtn.disabled = false;
                                    displayReport(step1Report);
                                    fillMsg.className = "msg msg-success";
                                    fillMsg.innerHTML = "✓ Поля текущего шага заполнены.<br><small>Проверьте данные и при необходимости перейдите к следующему шагу.</small>";
                                }
                            });
                        };
                    }

                    // 2. FILL CURRENT STEP ONLY (Single Pass)
                    fillStepBtn.onclick = () => {
                        fillStepBtn.disabled = true;
                        if (fillAutoBtn) fillAutoBtn.disabled = true;
                        fillMsg.className = "msg";
                        fillMsg.textContent = "Заполнение видимых полей формы...";

                        sendMessageToTabWithAutoInject(activeTab.id, { action: "fill_avito_form", package: pkg }, report => {
                            fillStepBtn.disabled = false;
                            if (fillAutoBtn) fillAutoBtn.disabled = false;
                            if (!report) {
                                fillMsg.className = "msg msg-error";
                                fillMsg.textContent = "Не удалось связаться со страницей формы. Обновите страницу (F5).";
                                return;
                            }

                            displayReport(report);
                            const categoryFilled = (report.filled || []).some(f => f.type === 'category-tile' || f.source === 'category');

                            fillMsg.className = "msg msg-success";
                            if (categoryFilled) {
                                fillMsg.innerHTML = `✓ Название заполнено и выбрана категория <strong>${catName}</strong>.<br><small>На следующем шаге параметров нажмите «Заполнить текущий шаг» для ввода цены, состояния и характеристик.</small>`;
                            } else {
                                fillMsg.innerHTML = `✓ Поля текущего шага заполнены.<br><small>Проверьте данные и при необходимости перейдите к следующему шагу.</small>`;
                            }
                        });
                    };

                    // Clear Draft from Avito Button
                    clearDraftFromAvitoBtn.onclick = async () => {
                        await clearSessionDraft();
                        fillActionsContainer.style.display = "none";
                        fillReportContainer.style.display = "none";
                        fillTitle.textContent = "Форма подачи Avito";
                        fillDetectInfo.innerHTML = "Черновик очищен.<br>Откройте карточку товара в Техноребут для создания нового черновика.";
                        fillMsg.textContent = "";
                    };
                } else {
                    fillTitle.textContent = "Форма подачи Avito";
                    fillDetectInfo.innerHTML = "Нет активного черновика.<br>Откройте карточку товара в Техноребут (<code>/inventory/products/{id}</code>) и нажмите <strong>«Подготовить для Avito»</strong>.";
                    fillActionsContainer.style.display = "none";
                    fillReportContainer.style.display = "none";
                }
                return;
            }

            // 3. CONTEXT C: Avito Pages (Listings / Single Ad)
            if (isAvitoHost) {
                actionSection.style.display = "block";
                pageDetectInfo.innerHTML = "Сканирование страницы Avito... <span style='font-size:11px;color:#888;'>(ожидание карточек)</span>";
                sendBtn.disabled = true;

                sendMessageToTabWithAutoInject(activeTab.id, { action: "extract_current_page", deepScan: false }, response => {
                    actionSection.style.display = "none";
                    if (!response) {
                        actionSection.style.display = "block";
                        pageDetectInfo.textContent = "Обновите страницу Avito (F5) для активации расширения.";
                        sendBtn.disabled = true;
                        return;
                    }

                    currentExtractionData = response;
                    if (response.error) {
                        actionSection.style.display = "block";
                        pageDetectInfo.textContent = response.error;
                        sendBtn.disabled = true;
                    } else if (response.page_type === "my_listings") {
                        setupBulkSection(activeTab, response);
                    } else {
                        setupSingleListingSection(activeTab, response);
                    }
                });
                return;
            }

            // 4. CONTEXT D: Generic / Other Pages
            actionSection.style.display = "block";
            pageTypeTitle.textContent = "Техноребут Avito";
            pageDetectInfo.innerHTML = "Откройте карточку товара в <strong>Техноребут</strong> (для публикации) или объявление на <strong>avito.ru</strong> (для импорта).";
            sendBtn.disabled = true;
        });
    }

    // Send Button click (Ingestion)
    sendBtn.addEventListener("click", () => {
        if (!isPaired) {
            resultMsg.className = "msg msg-error";
            resultMsg.textContent = "Расширение не привязано. Введите код подключения выше.";
            return;
        }

        sendBtn.disabled = true;
        resultMsg.className = "msg";
        resultMsg.textContent = "Сбор фото в HD и передача в Техноребут...";

        chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
            if (!tabs || tabs.length === 0) {
                sendBtn.disabled = false;
                resultMsg.className = "msg msg-error";
                resultMsg.textContent = "Активная вкладка не найдена.";
                return;
            }
            const activeTab = tabs[0];

            sendMessageToTabWithAutoInject(activeTab.id, { action: "extract_current_page", deepScan: true }, deepResponse => {
                const payloadToSend = (deepResponse && (deepResponse.listing || deepResponse.items)) ? deepResponse : currentExtractionData;
                if (!payloadToSend) {
                    sendBtn.disabled = false;
                    resultMsg.className = "msg msg-error";
                    resultMsg.textContent = "Не удалось извлечь данные со страницы.";
                    return;
                }

                const action = payloadToSend.page_type === "listing" ? "ingest_listing" : "ingest_my_listings";
                chrome.runtime.sendMessage({ action: action, payload: payloadToSend }, res => {
                    sendBtn.disabled = false;
                    if (res && res.success && res.product_id != null) {
                        const photosImported = res.photos_imported || (res.details && res.details.photos_imported) || 0;
                        const photosSkipped = res.photos_skipped || (res.details && res.details.photos_skipped) || 0;
                        const photosTotal = res.photos_total !== undefined ? res.photos_total : 
                            ((res.details && res.details.photos_total !== undefined) ? res.details.photos_total : 
                            (photosImported + photosSkipped));

                        if (openProductBtn && productLinkContainer) {
                            const targetUrl = `http://localhost:8011/inventory/products/${res.product_id}`;
                            openProductBtn.onclick = () => {
                                chrome.tabs.create({ url: targetUrl });
                            };
                            productLinkContainer.style.display = "block";
                        }

                        if (res.status === "partial" || (res.details && res.details.result === "partial")) {
                            resultMsg.className = "msg msg-warning";
                            resultMsg.innerHTML = `Основные данные обновлены, но фотографии импортировать не удалось.<br>Product ID: <strong>${res.product_id}</strong>`;
                        } else {
                            resultMsg.className = "msg msg-success";
                            if (photosImported > 0 && photosSkipped > 0) {
                                resultMsg.innerHTML = `✓ Объявление обновлено.<br>Product ID: <strong>${res.product_id}</strong><br>Добавлено новых фото: <strong>${photosImported}</strong> (всего в товаре: <strong>${photosTotal}</strong>)`;
                            } else if (photosImported === 0 && photosSkipped > 0) {
                                resultMsg.innerHTML = `✓ Карточка актуальна.<br>Product ID: <strong>${res.product_id}</strong><br>Все фотографии синхронизированы (всего: <strong>${photosTotal}</strong>)`;
                            } else {
                                resultMsg.innerHTML = `✓ Объявление импортировано.<br>Product ID: <strong>${res.product_id}</strong><br>Фотографий: <strong>${photosTotal}</strong>`;
                            }
                        }
                    } else {
                        resultMsg.className = "msg msg-error";
                        const errDetail = res && res.message ? res.message : "Ошибка импорта товара в Core API.";
                        resultMsg.innerHTML = `✕ Объявление получено, но импорт товара завершился ошибкой.<br>${errDetail}`;
                    }
                });
            });
        });
    });
});
