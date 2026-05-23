from ljp_page._module.request.brower.pydoll.constants import Scripts as _scripts

class Scripts(_scripts):
    MAKE_REQUEST = """
    (async function() {{
        async function makeRequest(url, options) {{
            try {{
                const response = await fetch(url, {{
                    ...options,
                    credentials: 'include'
                }});

                const headers = {{}};
                response.headers.forEach((value, key) => {{
                    headers[key] = value;
                }});

                const cookies = document.cookie;
                const contentType = response.headers.get('content-type') || '';

                // 核心修复：获取原始二进制
                const buffer = await response.arrayBuffer();
                const content = Array.from(new Uint8Array(buffer));

                let text = null;
                let json = null;

                try {{
                    text = await new Response(buffer).text();
                }} catch (e) {{
                    text = '';
                }}

                if (contentType.includes('application/json')) {{
                    try {{
                        json = JSON.parse(text);
                    }} catch (e) {{
                        json = null;
                    }}
                }}

                return {{
                    status: response.status,
                    ok: response.ok,
                    url: response.url,
                    headers: headers,
                    cookies: cookies,
                    content: content,
                    text: text,
                    json: json
                }};

            }} catch (error) {{
                return {{
                    error: error.toString(),
                    status: 0
                }};
            }}
        }}

        const url = {url};
        const options = {options};
        return await makeRequest(url, options);
    }})();
    """
