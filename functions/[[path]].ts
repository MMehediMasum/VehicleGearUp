export const onRequest: PagesFunction = async (context) => {
  const url = new URL(context.request.url);

  const isPagesDevHost =
    url.hostname === "vehiclegearup.pages.dev" ||
    url.hostname.endsWith(".vehiclegearup.pages.dev");

  if (isPagesDevHost) {
    url.hostname = "vehiclegearup.com";
    url.protocol = "https:";

    return Response.redirect(url.toString(), 301);
  }

  return context.next();
};
