FROM nginx:1.24-alpine

# RUN addgroup -S --gid ${GID:-1000} www && adduser -S -g ${GID:-1000} -u ${UID:-1000} www 
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d
RUN mkdir -p /www/data/staticfiles
# RUN chown -R www:www /www && chmod -R 755 /www && \
#         chown -R www:www /var/cache/nginx && \
#         chown -R www:www /var/log/nginx && \
#         chown -R www:www /etc/nginx/conf.d
# RUN touch /var/run/nginx.pid && \
#         chown -R www:www /var/run/nginx.pid
RUN echo WIP > /www/data/index.html
# USER www
