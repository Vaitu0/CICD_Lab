FROM nginx:1.31.5
# Config and site files are bind-mounted at runtime via compose:
#   ./nginx/conf.d → /etc/nginx/conf.d
#   ../apps/frontend → /usr/share/nginx/html
COPY ./conf.d/nginx.conf /etc/nginx/conf.d/default.conf
