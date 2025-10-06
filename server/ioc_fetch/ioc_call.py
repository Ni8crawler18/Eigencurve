from playwright.sync_api import sync_playwright
import time, os
from dotenv import load_dotenv

load_dotenv()

PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_PORT = os.getenv("PROXY_PORT")
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")
print(f"Proxy: {PROXY_HOST}:{PROXY_PORT} User: {PROXY_USER}")


def get_ip_info(ip):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        proxy_config = None
        if PROXY_HOST and PROXY_PORT:
            proxy_config = {"server": f"http://{PROXY_HOST}:{PROXY_PORT}"}
            if PROXY_USER and PROXY_PASS:
                proxy_config["username"] = PROXY_USER
                proxy_config["password"] = PROXY_PASS

        try:
            context = browser.new_context(proxy=proxy_config)
            page = context.new_page()
            page.goto("https://www.virustotal.com/gui/home/upload", timeout=30000)
        except Exception as e:
            print(f"[!] Proxy failed: {e}. Falling back to direct connection...")
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://www.virustotal.com/gui/home/upload", timeout=30000)

        # Enter the IP in the search box
        page.wait_for_selector("#searchInput, input[placeholder*='URL']", timeout=10000)
        if page.query_selector("#searchInput"):
            page.fill("#searchInput", ip)
            page.keyboard.press("Enter")
        else:
            page.fill("input[placeholder*='URL']", ip)
            page.keyboard.press("Enter")

        time.sleep(4)  # wait for the page to render

        info = page.evaluate("""
            () => {
                function traverse(root) {
                    let result = {
                        circles: [],
                        vendorMessage: null,
                        asn: null,
                        org: null,
                        country: null
                    };

                    try {
                        // Gauge circles
                        if(root.querySelectorAll) {
                            for(const c of root.querySelectorAll('circle')) {
                                let stroke = c.getAttribute('stroke') || '';
                                let computed = getComputedStyle(c).getPropertyValue('stroke') || '';
                                if(stroke.toLowerCase().includes('danger') ||
                                   stroke.toLowerCase().includes('success') ||
                                   computed.includes('255, 90, 80') ||
                                   computed.includes('0, 128, 0')) {
                                    result.circles.push({strokeAttr: stroke, strokeComputed: computed});
                                }
                            }
                        }

                        // Vendor message (malicious/benign)
                        if(!result.vendorMessage) {
                            const messages = root.querySelectorAll('div.hstack.gap-2.fw-bold.text-success, div.hstack.gap-2.fw-bold.text-danger');
                            if(messages.length > 0) {
                                result.vendorMessage = messages[0].innerText.trim();
                            }
                        }

                        // ASN, org, country (only relevant if malicious)
                        if(!result.asn || !result.org) {
                        // Find all <a> elements under div.hstack.gap-2
                        const asLinks = root.querySelectorAll('div.hstack.gap-2 > a');
                        for (const a of asLinks) {
                            const text = a.innerText.trim();
                            if(text.startsWith("AS ")) {
                                // Extract number after "AS "
                                const match = text.match(/AS\s+(\d+)/);
                                if(match){
                                    result.asn = match[1];
                                }
                                break; // stop after first match
                            }
                        }

                        // Find organization name
                        const orgSpan = root.querySelector('div.hstack.gap-2 > span a');
                        if(orgSpan) result.org = orgSpan.innerText.trim();
                    }
                        if(!result.country) {
                            const countryDiv = root.querySelector('#country');
                            if(countryDiv) result.country = countryDiv.innerText.trim();
                        }

                        // Recurse shadow roots
                        const nodes = root.querySelectorAll ? root.querySelectorAll('*') : [];
                        for(const n of nodes){
                            if(n.shadowRoot){
                                const child = traverse(n.shadowRoot);
                                result.circles.push(...child.circles);
                                if(!result.vendorMessage && child.vendorMessage) result.vendorMessage = child.vendorMessage;
                                if(!result.asn && child.asn) result.asn = child.asn;
                                if(!result.org && child.org) result.org = child.org;
                                if(!result.country && child.country) result.country = child.country;
                            }
                        }

                    } catch(e){}
                    return result;
                }

                return traverse(document);
            }
        """)

        # Determine BENIGN vs MALICIOUS
        classification = "UNKNOWN"
        flagged_count = None

        msg = info.get("vendorMessage", "")
        if msg.lower().startswith("no security vendor"):
            classification = "BENIGN"
        else:
            import re
            m = re.match(r"(\d+)/\d+", msg)
            if m:
                flagged_count = int(m.group(1))
                classification = "MALICIOUS"

        browser.close()

        if classification == "BENIGN":
            return {
                "ip": ip,
                "classification": "BENIGN"
            }

        return {
            "ip": ip,
            "classification": "MALICIOUS",
            "flagged": flagged_count,
            "asn": info.get("asn"),
            "org": info.get("org"),
            "country": info.get("country")
        }


if __name__ == "__main__":
    ip = "140.143.200.251"
    result = get_ip_info(ip)
    print(result)