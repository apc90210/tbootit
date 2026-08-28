// Technoreboot Avito Popup Script (v0.2.18)

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
        let manifestVer = "0.2.18";
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
                        const filledKeys = new Set(filled.map(f => f.source));
                        const unresFields = (r2.unresolved_fields || []).filter(u => !filledKeys.has(u.key));
                        const unresOptions = [...(r1.unresolved_options || []), ...(r2.unresolved_options || [])];
                        return {
                            product_id: r2.product_id || r1.product_id,
                            filled,
                            skipped_nonempty: skipped,
                            unresolved_fields: unresFields,
                            unresolved_options: unresOptions
                        };
                    }

                    function displayReport(report) {
                        fillReportContainer.style.display = "block";
                        const filledCount = (report.filled || []).length;
                        const skippedCount = (report.skipped_nonempty || []).length;
                        const unresFieldsCount = (report.unresolved_fields || []).length;
                        const unresOptionsCount = (report.unresolved_options || []).length;

                        fillSummary.innerHTML = `
                            <strong>Результат заполнения:</strong><br>
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
                            detailsHtml += "<strong>Не сопоставлены:</strong><br>" + report.unresolved_fields.map(u => `? ${u.key}: ${u.value}`).join("<br>");
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
                                    }, 1200);
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

            // 3. CONTEXT C: Avito Listing Page (Standard Ingestion)
            if (isAvitoHost) {
                actionSection.style.display = "block";
                sendMessageToTabWithAutoInject(activeTab.id, { action: "extract_current_page", deepScan: false }, response => {
                    if (!response) {
                        pageDetectInfo.textContent = "Обновите страницу Avito (F5) для активации расширения.";
                        sendBtn.disabled = true;
                        return;
                    }

                    currentExtractionData = response;
                    if (response.error) {
                        pageDetectInfo.textContent = response.error;
                        sendBtn.disabled = true;
                    } else if (response.page_type === "listing") {
                        pageTypeTitle.textContent = "Карточка объявления";
                        const item = response.listing || {};
                        const detectedPhotosCount = (item.photos && item.photos.length) || 0;
                        const displayTitle = item.title || "Объявление Avito";
                        const displayPrice = item.price ? item.price + " ₽" : "Не указана";
                        pageDetectInfo.innerHTML = `<strong>${displayTitle}</strong><br>ID: ${item.external_item_id || 'Авто'}<br>Цена: ${displayPrice}<br>Обнаружено фото: <strong>${detectedPhotosCount}</strong> <span style="color:#888; font-size:11px;">(сканирование HD...)</span>`;
                        
                        if (isPaired) {
                            sendBtn.disabled = false;
                            sendBtn.textContent = "Передать объявление в Техноребут";
                            resultMsg.textContent = "";
                        } else {
                            sendBtn.disabled = true;
                            sendBtn.textContent = "Передать объявление в Техноребут";
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
                    } else if (response.page_type === "my_listings") {
                        pageTypeTitle.textContent = "Мои объявления";
                        pageDetectInfo.textContent = `Обнаружено объявлений на странице: ${response.listings_count || 0}`;
                        if (isPaired) {
                            sendBtn.disabled = false;
                            sendBtn.textContent = "Передать список в Техноребут";
                            resultMsg.textContent = "";
                        }
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
