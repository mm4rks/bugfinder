FROM nginx:1.24-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d
# RUN addgroup -S --gid ${GID:-1000} nginx && adduser -S -g ${GID:-1000} -u ${UID:-1000} nginx
# RUN mkdir -p /www/data/staticfiles
# RUN chown -R nginx:nginx /www && chmod -R 755 /www && \
#         chown -R nginx:nginx /var/cache/nginx && \
#         chown -R nginx:nginx /var/log/nginx && \
#         chown -R nginx:nginx /etc/nginx/conf.d
# RUN touch /var/run/nginx.pid && \
#         chown -R nginx:nginx /var/run/nginx.pid
# USER www
