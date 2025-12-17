import datetime as dt
import webcolors as webcls
from rest_framework import serializers

from .models import Achievement, AchievementCat, Cat, Owner, CHOICES


class AchievementSerializer(serializers.ModelSerializer):
    #переопределяем название поля 'name'
    achievement_name = serializers.CharField(source='name')

    class Meta:
        model = Achievement
        fields = ('achievement_name',)


class Hex2NameColor(serializers.Field):
    """
    Для создания собственного типа поля сериализатора нужно описать класс
    для нового типа, который будет унаследован от serializers.Field
    и описать в нём два метода: def to_representation(self, value) (для чтения)
    и def to_internal_value(self, data) (для записи)
    """
    # При чтении данных ничего не меняем - просто возвращаем как есть
    def to_representation(self, value):
        return value
    # При записи код цвета конвертируется в его название
    def to_internal_value(self, data):
        # Доверяй, но проверяй
        try:
            # Если имя цвета существует, то конвертируем код в название
            data = webcls.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class CatSerializer(serializers.ModelSerializer):
    # owner = serializers.PrimaryKeyRelatedField(
    #     read_only=True,
    #     # default=serializers.CurrentUserDefault()
    # )
    achievements = AchievementSerializer(many=True, required=False)
    age = serializers.SerializerMethodField()
    # color = Hex2NameColor()  # Вот он - наш собственный тип поля
    color = serializers.ChoiceField(choices=CHOICES)  # Выбор цветов из списка (можно сделать на уровне модели)

    class Meta:
        model = Cat
        fields = (
            'id', 'name', 'color', 'birth_year', 'owner', 'achievements', 'age'
            )

    def get_age(self, obj):
        return dt.datetime.now().year - obj.birth_year

    def create(self, validated_data):
        # Если в исходном запросе не было поля achievements
        if 'achievements' not in self.initial_data:
            # То создаём запись о котике без его достижений
            cat = Cat.objects.create(**validated_data)
            return cat

        # Иначе делаем следующее:
        # Уберём список достижений из словаря validated_data и сохраним его
        achievements = validated_data.pop('achievements')
        # Сначала добавляем котика в БД
        cat = Cat.objects.create(**validated_data)
        # А потом добавляем его достижения в БД
        for achievement in achievements:
            current_achievement, created = Achievement.objects.get_or_create(
                **achievement)
            # И связываем каждое достижение с этим котиком
            AchievementCat.objects.create(
                achievement=current_achievement, cat=cat)
        return cat 


class CatListSerializer(serializers.ModelSerializer):
    """For work with list of objects."""
    
    color = serializers.ChoiceField(choices=CHOICES)

    class Meta:
        model = Cat
        fields = ('id', 'name', 'color')


class OwnerSerializer(serializers.ModelSerializer):
    cats = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Owner
        fields = ('first_name', 'last_name', 'cats')
