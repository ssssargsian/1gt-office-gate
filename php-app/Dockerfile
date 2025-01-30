FROM php:8.2-cli

WORKDIR /var/www/html

RUN apt-get update && apt-get install -y unzip curl \
    && docker-php-ext-install pdo pdo_mysql

COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

COPY . ./

CMD ["php", "-S", "0.0.0.0:8000", "-t", "public"]