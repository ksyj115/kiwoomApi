import time
from PyQt5.QtCore import QEventLoop
from logger import logger
from config import Config

class Trading:
    """거래 기능 클래스"""
    
    def __init__(self, kiwoom_api):
        self.api = kiwoom_api
        self.order_event_loop = QEventLoop()
        self.order_result = {}
        
        # 이벤트 핸들러 연결
        self._connect_trading_events()
        
        logger.info("거래 기능 초기화 완료")
    
    def _connect_trading_events(self):
        """거래 관련 이벤트 핸들러 연결"""
        self.api.ocx.OnReceiveChejanData.connect(self._on_receive_chejan_data)
        self.api.ocx.OnReceiveMsg.connect(self._on_receive_msg)
        
        logger.debug("거래 이벤트 핸들러 연결 완료")
    
    def buy_stock(self, code, quantity, price=0, order_type="시장가"):
        """주식 매수 주문"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return False
            
            if Config.is_simulation_mode():
                logger.info(f"시뮬레이션 모드: {code} 매수 {quantity}주")
                return True
            
            # 주문 타입 설정
            if order_type == "시장가":
                order_type_code = "1"
            elif order_type == "지정가":
                order_type_code = "00"
            else:
                logger.error(f"지원하지 않는 주문 타입: {order_type}")
                return False
            
            # 주문 실행
            result = self.api.ocx.SendOrder(
                "매수주문",
                "0101",  # 화면번호
                self.api.get_login_info("ACCOUNT_CNT"),  # 계좌번호
                1,  # 주문타입 (1:신규매수)
                code,  # 종목코드
                quantity,  # 주문수량
                price,  # 주문가격
                order_type_code,  # 거래구분
                ""  # 원주문번호
            )
            
            if result == 0:
                logger.log_trade("매수", code, quantity, price, quantity * price)
                return True
            else:
                logger.log_error("BUY_ORDER", f"매수 주문 실패 (에러코드: {result})")
                return False
                
        except Exception as e:
            logger.log_error("BUY_STOCK", str(e))
            return False
    
    def sell_stock(self, code, quantity, price=0, order_type="시장가"):
        """주식 매도 주문"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return False
            
            if Config.is_simulation_mode():
                logger.info(f"시뮬레이션 모드: {code} 매도 {quantity}주")
                return True
            
            # 주문 타입 설정
            if order_type == "시장가":
                order_type_code = "1"
            elif order_type == "지정가":
                order_type_code = "00"
            else:
                logger.error(f"지원하지 않는 주문 타입: {order_type}")
                return False
            
            # 주문 실행
            result = self.api.ocx.SendOrder(
                "매도주문",
                "0102",  # 화면번호
                self.api.get_login_info("ACCOUNT_CNT"),  # 계좌번호
                2,  # 주문타입 (2:신규매도)
                code,  # 종목코드
                quantity,  # 주문수량
                price,  # 주문가격
                order_type_code,  # 거래구분
                ""  # 원주문번호
            )
            
            if result == 0:
                logger.log_trade("매도", code, quantity, price, quantity * price)
                return True
            else:
                logger.log_error("SELL_ORDER", f"매도 주문 실패 (에러코드: {result})")
                return False
                
        except Exception as e:
            logger.log_error("SELL_STOCK", str(e))
            return False
    
    def cancel_order(self, order_no, code, quantity):
        """주문 취소"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return False
            
            if Config.is_simulation_mode():
                logger.info(f"시뮬레이션 모드: 주문 취소 {order_no}")
                return True
            
            # 주문 취소
            result = self.api.ocx.SendOrder(
                "주문취소",
                "0103",  # 화면번호
                self.api.get_login_info("ACCOUNT_CNT"),  # 계좌번호
                3,  # 주문타입 (3:취소주문)
                code,  # 종목코드
                quantity,  # 주문수량
                0,  # 주문가격
                "1",  # 거래구분
                order_no  # 원주문번호
            )
            
            if result == 0:
                logger.info(f"주문 취소 요청: {order_no}")
                return True
            else:
                logger.log_error("CANCEL_ORDER", f"주문 취소 실패 (에러코드: {result})")
                return False
                
        except Exception as e:
            logger.log_error("CANCEL_ORDER", str(e))
            return False
    
    def get_stock_price(self, code):
        """현재가 조회"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return 0
            
            price = self.api.get_master_last_price(code)
            try:
                price = float(price.replace(',', ''))  # 혹시 천 단위 콤마가 있을 경우 제거
            except (ValueError, AttributeError):
                price = 0
            
            if price > 0:
                logger.debug(f"{code} 현재가: {price:,}원")
                return price
            else:
                logger.warning(f"{code} 현재가 조회 실패")
                return 0
                
        except Exception as e:
            logger.log_error("GET_STOCK_PRICE", str(e))
            return 0
    
    def get_stock_name(self, code):
        """종목명 조회"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return ""
            
            name = self.api.get_master_code_name(code)
            if name:
                logger.debug(f"{code} 종목명: {name}")
                return name
            else:
                logger.warning(f"{code} 종목명 조회 실패")
                return ""
                
        except Exception as e:
            logger.log_error("GET_STOCK_NAME", str(e))
            return ""
    
    def get_account_info(self):
        """계좌 정보 조회"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return {}
            
            account_info = {
                "계좌번호": self.api.get_login_info("ACCOUNT_CNT"),
                "사용자ID": self.api.get_login_info("USER_ID"),
                "사용자명": self.api.get_login_info("USER_NAME"),
                "서버구분": self.api.get_login_info("SERVER_GUBUN"),
                "키움서버": self.api.get_login_info("KEY_BSECGB"),
                "방화벽": self.api.get_login_info("FIREW_SECGB")
            }
            
            logger.info("계좌 정보 조회 완료")
            return account_info
            
        except Exception as e:
            logger.log_error("GET_ACCOUNT_INFO", str(e))
            return {}
    
    def _on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """체결잔고 데이터 수신"""
        try:
            if gubun == "0":  # 주문체결통보
                logger.debug("주문체결통보 수신")
            elif gubun == "1":  # 잔고통보
                logger.debug("잔고통보 수신")
            elif gubun == "3":  # 특이신호
                logger.debug("특이신호 수신")
            elif gubun == "4":  # 주문체결통보
                logger.debug("주문체결통보 수신")
            
        except Exception as e:
            logger.log_error("CHEJAN_DATA", str(e))
    
    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        """메시지 수신"""
        try:
            logger.info(f"거래 메시지: {msg}")
            
            # 주문 관련 메시지 처리
            if "주문" in msg:
                if "성공" in msg:
                    logger.info("주문이 성공적으로 처리되었습니다.")
                elif "실패" in msg:
                    logger.error("주문 처리에 실패했습니다.")
            
        except Exception as e:
            logger.log_error("RECEIVE_MSG", str(e)) 