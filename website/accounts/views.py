import datetime
from django.contrib.sessions.models import Session
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from accounts.forms import SignUpForm
from accounts.models import UserModel, DayLoginCompleteTime, LoginTime
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from random import randint


def login_view(request):  # kullanıcının giriş yapacağı sayfa
    if request.method == 'POST':  # kullanıcı giriş yapmak için kullanıcı adı ve şifresini gönderdi
        form = AuthenticationForm(data=request.POST)  # django form kullanarak kullanıcı belirlendi
        if form.is_valid():  # gönderilen verilerde bir sorun oluşmadıysa
            user = form.get_user()  # kullanıcıyı belirle
            if user.usermodel.is_activated:  # kullanıcı hesabını aktif etmiş ise
                current_session = Session.objects.get(session_key=request.session.session_key)  # mevcut session'ı al
                login_time_object = current_session.logintime_set.all()  # mevcut session'a ait giriş nesnesini al
                login_time = login_time_object.first().beginning_time  # giriş zamanını al
                now_time = datetime.datetime.now()  # şuanki zamanı al
                b_time = datetime.timedelta(hours=login_time.hour, minutes=login_time.minute, seconds=login_time.second)
                e_time = datetime.timedelta(hours=now_time.hour, minutes=now_time.minute, seconds=now_time.second)
                time_by_seconds = (e_time - b_time).seconds  # aradaki farkı saniyeler cinsinden hesapla
                try:  # bugünki giriş zamanı nesnesine erişmeye çalış
                    today_login_time = DayLoginCompleteTime.objects.get(
                        day=datetime.date(now_time.year, now_time.month, now_time.day)
                    )  # bugünki giriş zamanı nesnesini al
                    new_average = (today_login_time.user_count * today_login_time.average + time_by_seconds) / \
                                  (today_login_time.user_count + 1)  # yeni ortalamayı hesapla
                    today_login_time.average = new_average  # yeni ortalamayı gir
                    today_login_time.user_count = today_login_time.user_count + 1  # giriş yapılma sayısını 1 arttır
                    today_login_time.save()  # yeni giriş zamanı nesnesini veritabanına kaydet
                except DayLoginCompleteTime.DoesNotExist:  # bugün için henüz giriş zamanı nesnesi oluşturulmadıysa
                    DayLoginCompleteTime.objects.create(day=datetime.date(now_time.year, now_time.month, now_time.day),
                                                        average=time_by_seconds)  # yeni giriş zamanı nesnesi oluştur
                login(request, user)  # kullanıcıyı giriş yaptır
                return redirect('/success/')
            else:  # kullanıcı hesabını aktif etmemiş ise
                return redirect('/activate/')  # kullanıcıyı hesap aktifleştirme sayfasına yönlendir
        else:  # kullanıcı adı veya şifre hatalı ise
            return render(request, 'accounts/login.html', {'error': True})  # hata olduğunu bildir
    else:  # kullanıcı sayfaya girdiğinde
        if not request.session.exists(request.session.session_key):  # kullanıcıya ait bir session yok ise
            request.session.create()  # yeni bir session oluştur
        current_session = Session.objects.get(session_key=request.session.session_key)  # mevcut session nesnesine eriş
        # mevcut session nesnesine ait giriş zamanı nesnesi var ise, bu durumda kullanıcı giriş yapmadan sayfadan
        # ayrılmış olabilir, veya bağlantıda bir sorun oluşmuş olabilir
        if LoginTime.objects.filter(session=current_session).exists():
            login_time_object = LoginTime.objects.get(session=current_session)
            login_time_object.beginning_time = datetime.datetime.now()  # giriş zamanını yeni zaman ile değiştir
            login_time_object.save()
        else:  # giriş zamanı nesnesi yok ise oluştur
            LoginTime.objects.create(session=current_session, beginning_time=datetime.datetime.now())
    return render(request, 'accounts/login.html')


def signup_view(request):  # kullanıcıların kayıt olması için gerekli sayfa
    if request.method == 'POST':  # kullanıcı kayıt olmak için gerekli bilgileri girdiğinde
        form = SignUpForm(request.POST)  # gelen bilgiler forma gönderilir
        if form.is_valid():  # eğer bilgilerde bir sorun yoksa
            form.save()  # kullanıcıyı kaydet
            username = form.cleaned_data.get('username')  # kullanıcı adını al
            raw_password = form.cleaned_data.get('password1')  # şifreyi al
            user = authenticate(username=username, password=raw_password)  # kullanıcıyı belirle
            activation_code = str(randint(10000, 100000))  # aktivasyon kodunu belirle
            UserModel.objects.create(user=user,
                                     activation_code=activation_code,
                                     is_activated=False
                                     )  # kullanıcının aktivasyon bilgilerini kaydet
            subject = "Activation Code"
            email_template_name = "accounts/activation_template.txt"
            c = {
                "activation_code": activation_code,
                "user": user.username,
            }
            email = render_to_string(email_template_name, c)
            try:  # mail göndermeyi dene
                send_mail(subject, email, 's.burgazoglu@gmail.com', [user.email], fail_silently=False)
            except BadHeaderError:  # eğer bir problem ile karşılaşılırsa
                return HttpResponse('Invalid header found.')
            #send_mail('Activation Mail',  # aktivasyon mailini gönder
            #          'Your activation code is : ' + activation_code,
            #          's.burgazoglu@gmail.com',
            #          [form.cleaned_data.get('email')],
            #          fail_silently=False,
            #          )
            login(request, user)  # kullanıcıya giriş yaptır
            return redirect('/activate/')  # kullanıcıyı aktivasyon sayfasına gönder
        else:
            form = SignUpForm()
            return render(request, 'accounts/signup.html', {'form': form, 'error': True})  # kullanıcıyı bilgilendir
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})  # sayfayı göster


def password_reset_view(request):  # şifre değiştirme sayfası
    if request.method == "POST":  # şifre değiştirilmesi için mail gönderildiğinde
        password_reset_form = PasswordResetForm(request.POST)  # forma gönderilir
        if password_reset_form.is_valid():  # eğer form da bir sorun yok ise
            data = password_reset_form.cleaned_data['email']  # kullanıcının mailini al
            associated_users = User.objects.filter(Q(email=data))  # maile ait kullanıcıları al
            if associated_users.exists():  # eğer bu maile ait kullanıcı var ise
                for user in associated_users:  # herbir kullanıcı için
                    subject = "Password Reset Requested"
                    email_template_name = "accounts/password_email_template.txt"
                    c = {
                        "email": user.email,
                        'domain': '127.0.0.1:8000',
                        'site_name': 'Website',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http',
                    }
                    email = render_to_string(email_template_name, c)
                    try:  # mail göndermeyi dene
                        send_mail(subject, email, 's.burgazoglu@gmail.com', [user.email], fail_silently=False)
                    except BadHeaderError:  # eğer bir problem ile karşılaşılırsa
                        return HttpResponse('Invalid header found.')
                    return redirect("/accounts/password_reset/done/")
    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="accounts/password_reset.html",
                  context={"password_reset_form": password_reset_form})
